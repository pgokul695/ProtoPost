"""
Core routing engine with load balancing and failover.
Implements sandbox mode, manual load balancing, and smart failover.
"""

import json
import logging
import random
import traceback
from datetime import datetime
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from .models import EmailPayload, EmailLog
from .config_manager import config_manager
from .database import database_manager
from . import providers

logger = logging.getLogger("protopost")


class RoutingEngine:
    """
    Core email routing engine.
    Handles provider selection, load balancing, failover, and sandbox mode.
    """
    
    @staticmethod
    async def route(payload: EmailPayload) -> dict:
        """
        Main routing entry point.
        
        Args:
            payload: Email to send
        
        Returns:
            dict: Routing result with status, provider info, and timing
        
        Raises:
            HTTPException: If no providers are configured or all providers fail
        """
        start_time = datetime.now()
        
        # Load fresh config on every request
        config = await config_manager.load()
        
        # Sandbox mode check - intercept all emails locally
        if config.routing.sandbox:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            log = EmailLog(
                timestamp=datetime.utcnow().isoformat() + "Z",
                to_addresses=json.dumps(payload.to),
                from_address=payload.from_address,
                subject=payload.subject,
                provider_id=None,
                provider_name="Sandbox",
                status="sandbox",
                processing_time_ms=processing_time,
                request_payload=payload.model_dump_json(),
                response_payload=json.dumps({"intercepted": True, "mode": "sandbox"}),
                error_trace=None
            )
            
            await run_in_threadpool(database_manager.insert_log, log)
            
            return {
                "status": "sandbox",
                "message": "Email intercepted by Sandbox Mode (not sent externally)",
                "log_id": log.id,
                "processing_time_ms": processing_time
            }
        
        # Filter enabled providers
        active_providers = [p for p in config.providers if p.enabled]
        
        if not active_providers:
            raise HTTPException(
                status_code=503,
                detail="No active email providers configured. Please add and enable at least one provider."
            )
        
        # Attempt delivery based on routing mode
        if config.routing.mode == "manual":
            # Manual mode: one provider, one attempt — no fallback
            provider = RoutingEngine._select_manual(active_providers)
            try:
                result = await providers.dispatch(payload, provider)
                processing_time = (datetime.now() - start_time).total_seconds() * 1000

                log = EmailLog(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    to_addresses=json.dumps(payload.to),
                    from_address=payload.from_address,
                    subject=payload.subject,
                    provider_id=provider.id,
                    provider_name=provider.name,
                    status="success",
                    processing_time_ms=processing_time,
                    request_payload=payload.model_dump_json(),
                    response_payload=json.dumps(result),
                    error_trace=None
                )
                await run_in_threadpool(database_manager.insert_log, log)

                return {
                    "status": "success",
                    "message": f"Email sent successfully via {provider.name}",
                    "provider": {
                        "id": provider.id,
                        "name": provider.name,
                        "type": provider.type
                    },
                    "log_id": log.id,
                    "processing_time_ms": processing_time,
                    "message_id": result.get("message_id")
                }

            except Exception as e:
                logger.error(
                    "Manual mode provider %s failed: %s", provider.id, e, exc_info=True
                )
                processing_time = (datetime.now() - start_time).total_seconds() * 1000

                log = EmailLog(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    to_addresses=json.dumps(payload.to),
                    from_address=payload.from_address,
                    subject=payload.subject,
                    provider_id=provider.id,
                    provider_name=provider.name,
                    status="failed",
                    processing_time_ms=processing_time,
                    request_payload=payload.model_dump_json(),
                    response_payload=json.dumps({"error": str(e)}),
                    error_trace=traceback.format_exc()
                )
                await run_in_threadpool(database_manager.insert_log, log)

                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": f"Provider {provider.id} failed: {str(e)}",
                        "log_id": log.id,
                        "processing_time_ms": processing_time,
                    }
                )

        else:
            # Smart mode: sort by weight, attempt in order, stop on first success
            providers_to_try = sorted(active_providers, key=lambda p: p.weight, reverse=True)
            errors = []

            for provider in providers_to_try:
                try:
                    result = await providers.dispatch(payload, provider)

                    processing_time = (datetime.now() - start_time).total_seconds() * 1000

                    log = EmailLog(
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        to_addresses=json.dumps(payload.to),
                        from_address=payload.from_address,
                        subject=payload.subject,
                        provider_id=provider.id,
                        provider_name=provider.name,
                        status="success",
                        processing_time_ms=processing_time,
                        request_payload=payload.model_dump_json(),
                        response_payload=json.dumps(result),
                        error_trace=None
                    )
                    await run_in_threadpool(database_manager.insert_log, log)

                    return {
                        "status": "success",
                        "message": f"Email sent successfully via {provider.name}",
                        "provider": {
                            "id": provider.id,
                            "name": provider.name,
                            "type": provider.type
                        },
                        "log_id": log.id,
                        "processing_time_ms": processing_time,
                        "message_id": result.get("message_id")
                    }

                except Exception as e:
                    logger.error(
                        "Smart mode provider %s failed: %s", provider.id, e, exc_info=True
                    )
                    errors.append({
                        "provider_id": provider.id,
                        "provider_name": provider.name,
                        "error": str(e),
                    })
                    continue

            # All smart-mode providers failed
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            log = EmailLog(
                timestamp=datetime.utcnow().isoformat() + "Z",
                to_addresses=json.dumps(payload.to),
                from_address=payload.from_address,
                subject=payload.subject,
                provider_id=None,
                provider_name="All providers failed",
                status="failed",
                processing_time_ms=processing_time,
                request_payload=payload.model_dump_json(),
                response_payload=json.dumps({"errors": errors}),
                error_trace=traceback.format_exc()
            )
            await run_in_threadpool(database_manager.insert_log, log)

            raise HTTPException(
                status_code=502,
                detail={
                    "message": "All email providers failed",
                    "log_id": log.id,
                    "processing_time_ms": processing_time,
                    "errors": errors,
                }
            )
    
    @staticmethod
    def _select_manual(providers: list) -> object:
        """
        Select a provider using weighted random selection (manual mode).
        
        Args:
            providers: List of active providers with weight fields
        
        Returns:
            Provider: Selected provider
        """
        # Extract weights and normalize if needed
        weights = [p.weight for p in providers]
        total_weight = sum(weights)
        
        # If weights sum to 0, treat all equally
        if total_weight == 0:
            weights = [1] * len(providers)
            total_weight = len(providers)
        
        # Normalize weights if they don't sum to 100 (still maintain proportions)
        # random.choices handles non-normalized weights automatically
        
        selected = random.choices(providers, weights=weights, k=1)[0]
        return selected


# Global instance
routing_engine = RoutingEngine()
