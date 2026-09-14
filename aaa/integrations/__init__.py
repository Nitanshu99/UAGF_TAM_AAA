"""Partner-service integrations (S6 XAI, S7 Security) behind switchable providers.

Each component is selected independently via ``aaa.settings`` (mode
``internal`` runs this repo's built-in capabilities; ``external`` POSTs the
audit-state hand-off JSON to the partner API). Reports and the UI consume the
resulting evidence source-agnostically — customers never see S6/S7 branding.
"""
