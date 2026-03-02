# Contributing

ProtoPost is a hackathon tool, built by people under time pressure for other people under time pressure. Contributions are welcome — especially if you found a bug or missing provider during your own hackathon.

---

## Ways to contribute

- **Add a new email provider** — There's a clear pattern. See the checklist below.
- **Improve TROUBLESHOOTING.md** — If you hit an error that wasn't in the docs, add it.
- **Add a new setup walkthrough** — The Gmail and Resend wizards in the dashboard can be extended to other providers.
- **Fix a bug you found** — Open a PR with a clear description of what broke and what you changed.
- **Improve error messages** — If a provider returns a cryptic error, add a human-readable explanation.

---

## How to add a new email provider

Adding a provider involves five files. Follow this checklist in order:

**Step 1 — Add the provider type to the enum**

In `backend/models.py`, add your provider to the `ProviderType` enum:

```python
class ProviderType(str, Enum):
    resend = "resend"
    mailtrap = "mailtrap"
    gmail = "gmail"
    custom_smtp = "custom_smtp"
    yourprovider = "yourprovider"  # ← add this
```

**Step 2 — Add credential fields to the Provider model**

In `backend/models.py`, add the fields your provider needs and update the `@model_validator` to validate them:

```python
class Provider(BaseModel):
    # ... existing fields ...
    yourprovider_api_key: Optional[str] = None  # ← add your fields

    @model_validator(mode='after')
    def validate_credentials(self):
        if self.type == ProviderType.yourprovider:
            if not self.yourprovider_api_key:
                raise ValueError("yourprovider_api_key is required")
        return self
```

**Step 3 — Implement the send function**

In `backend/providers.py`, add a new async function:

```python
async def send_via_yourprovider(provider: Provider, payload: EmailPayload) -> str:
    """Returns the message ID on success, raises on failure."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.yourprovider.com/send",
            headers={"Authorization": f"Bearer {provider.yourprovider_api_key}"},
            json={
                "from": payload.from_addr,
                "to": payload.to,
                "subject": payload.subject,
                "html": payload.body_html,
                "text": payload.body_text,
            }
        )
        response.raise_for_status()
        return response.json().get("id", "")
```

**Step 4 — Add a case to the dispatch function**

In `backend/providers.py`, find the `dispatch()` function and add your provider:

```python
async def dispatch(provider: Provider, payload: EmailPayload) -> str:
    if provider.type == ProviderType.resend:
        return await send_via_resend(provider, payload)
    elif provider.type == ProviderType.mailtrap:
        return await send_via_mailtrap(provider, payload)
    # ...
    elif provider.type == ProviderType.yourprovider:  # ← add this
        return await send_via_yourprovider(provider, payload)
    else:
        raise ValueError(f"Unknown provider type: {provider.type}")
```

**Step 5 — Add the form fields to the dashboard**

In `frontend/dashboard.html`, find the `updateProviderFormFields()` function and add a case:

```javascript
} else if (type === 'yourprovider') {
    container.innerHTML = `
        <div>
            <label class="block text-sm font-medium mb-2">API Key</label>
            <div class="relative">
                <input type="password" id="yourproviderApiKey" 
                       value="${provider?.yourprovider_api_key || ''}" 
                       required class="w-full px-4 py-2 bg-slate-700 border border-slate-600 
                                       rounded-lg focus:outline-none focus:border-indigo-500 pr-10">
                <button type="button" onclick="togglePasswordVisibility('yourproviderApiKey')" 
                        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                    👁
                </button>
            </div>
        </div>
    `;
}
```

Also add the field collection in the `saveProvider()` function:

```javascript
} else if (type === 'yourprovider') {
    providerData.yourprovider_api_key = document.getElementById('yourproviderApiKey').value;
}
```

And add the option to the `<select>`:

```html
<option value="yourprovider">YourProvider</option>
```

**Step 6 — Document it**

Add your provider to the comparison table in [docs/PROVIDERS.md](docs/PROVIDERS.md) and write a setup section. Use the existing providers as a template.

**Step 7 — Test with a real account**

Create a free account on your provider, send a real email through the gateway, and make sure it arrives. Document any quirks you discover.

---

## Running the Test Suite Before Contributing

All pull requests must pass the existing test suite without modification.
Before opening a PR, run:

```bash
pip install -r requirements-test.txt
pytest tests/
```

New provider integrations require corresponding mock tests in
`tests/test_providers.py`. New API endpoints require tests in `tests/test_api.py`.
Do not open a PR with failing or skipped tests.

## Code Style Notes

These rules apply to all contributions:

**Backend (Python)**
- All async functions must be consistently awaited at every call site.
- Synchronous operations (database writes, file I/O) inside async functions
  must be offloaded with `run_in_threadpool` or protected with `asyncio.Lock`.
- All public functions require type hints.
- Follow PEP 8 formatting.

**Frontend (JavaScript)**
- Use native ES modules only. No bundler, no build step, no frameworks.
- Use `escapeHtml()` from `js/utils.js` whenever untrusted data is inserted
  into the DOM. Direct assignment to `innerHTML` with raw user data is not
  permitted.
- Remove all `console.log` statements before opening a PR.
- Keep import paths relative (e.g. `./api.js`, `./components/toast.js`).

**General**
- Do not commit `config.json` or `emails.db`. Both are covered by `.gitignore`.
- Do not add new runtime dependencies without discussion in an issue first.

---

## Running in dev mode

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Start with hot reload
uvicorn backend.main:app --reload --port 8000
```

The server reloads automatically when you change Python files. Changes to frontend files under `frontend/` take effect on next browser refresh.

---

## Opening a PR

- Describe what you changed and why in the PR description
- If you added a provider, include the name of a successful test send in the description (no credentials needed — just "tested with Postmark sandbox account" is fine)
- Don't worry about a perfect commit history — squash commits are fine

That's it. No CLA, no formal review process, no CI gate to pass. This is a hackathon tool.
