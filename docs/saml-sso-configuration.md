# SAML 2.0 Single Sign-On (SSO) Configuration

*Note: SAML SSO is available exclusively on FlowBoard **Team** plans.*

## Supported Identity Providers
- Okta, Microsoft Azure AD (Entra ID), Google Workspace, OneLogin, PingIdentity.

## Configuration Steps
1. Navigate to **Workspace Settings > Security > Single Sign-On**.
2. Copy the **ACS URL** (\https://auth.flowboard.app/saml/consume/[workspace_id]\) and **Entity ID** (\https://auth.flowboard.app/saml/metadata\).
3. In your IdP, create a new SAML 2.0 application and paste the ACS URL and Entity ID.
4. Download your IdP Metadata XML or copy the Identity Provider Issuer URL, SSO Endpoint, and X.509 Certificate into FlowBoard.
5. Enable **Enforce SSO** to mandate login via IdP for all non-guest users.
