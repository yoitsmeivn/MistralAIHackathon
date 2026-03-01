-- 008_update_script_system_prompts.sql
-- Update all existing scripts to use target environment context in system_prompt
-- (seed migrations used ON CONFLICT DO NOTHING, so existing rows were never updated)

-- 002_seed.sql scripts (301-304)
UPDATE scripts SET system_prompt = 'Target environment uses Active Directory for authentication, Microsoft 365 for email, and Okta SSO for single sign-on. MFA is enforced via Okta Verify push notifications. IT support tickets are managed through ServiceNow. Employees are accustomed to periodic password rotation prompts every 90 days.'
WHERE id = '00000000-0000-0000-0000-000000000301';

UPDATE scripts SET system_prompt = 'Target organization uses SAP for ERP and wire transfers require dual authorization through the Treasury Management System (TMS). Approvals over $10,000 need CFO sign-off via DocuSign. Finance team uses Bloomberg Terminal for transaction verification. Board-level acquisitions are handled under NDA with outside counsel.'
WHERE id = '00000000-0000-0000-0000-000000000302';

UPDATE scripts SET system_prompt = 'Target employees use corporate banking through Chase Business with online portal access. Direct deposit is set up via Workday payroll. Employees have personal and corporate accounts at various banks. Fraud alerts are typically sent via SMS and email, not phone calls. Bank''s legitimate fraud line requires callback verification.'
WHERE id = '00000000-0000-0000-0000-000000000303';

UPDATE scripts SET system_prompt = 'Target organization uses Workday for HRIS and benefits administration. Open enrollment runs annually in November. Benefits changes require employee self-service through the Workday portal. Direct deposit updates go through ADP payroll integration. HR verifications are normally handled via email with manager approval.'
WHERE id = '00000000-0000-0000-0000-000000000304';

-- 005_healthcare_script_seed.sql (305)
UPDATE scripts SET system_prompt = 'Target facility runs Epic EHR on Citrix virtual desktops. Authentication is through Active Directory with Imprivata single sign-on at workstations. VPN access uses Cisco AnyConnect. The organization is HIPAA-regulated and underwent a compliance audit last quarter. Patch management is handled through SCCM with monthly maintenance windows. Workstation PINs are 6-digit codes used for Imprivata tap-and-go badges.'
WHERE id = '00000000-0000-0000-0000-000000000305';

-- 006_campaign_scripts_seed.sql — Campaign 1: Finance (306-310)
UPDATE scripts SET system_prompt = 'Target organization uses SAP for ERP and accounts payable. Wire transfers require dual authorization through Treasury Management System. Bank routing numbers are stored in SAP vendor master records. Insurance claims are processed through a third-party portal. Refunds over $5,000 require controller sign-off.'
WHERE id = '00000000-0000-0000-0000-000000000306';

UPDATE scripts SET system_prompt = 'Target organization uses SAP for accounts payable and Coupa for procurement. Payment approval codes are 8-digit alphanumeric codes generated in SAP. Vendor invoices over $2,500 require a PO match. Late payment penalties are governed by net-30 terms in vendor contracts.'
WHERE id = '00000000-0000-0000-0000-000000000307';

UPDATE scripts SET system_prompt = 'Target organization uses ADP for payroll and direct deposit. Bonus payouts are processed quarterly through Workday compensation module. Direct deposit changes require employee self-service through the ADP portal with email confirmation. Finance team has read access to payroll records.'
WHERE id = '00000000-0000-0000-0000-000000000308';

UPDATE scripts SET system_prompt = 'Target organization uses NetSuite for accounting with Okta SSO integration. Passwords are managed through Active Directory with 90-day rotation. Patch management is handled by IT through SCCM. Finance workstations run on a segregated VLAN. Emergency patches require change advisory board approval.'
WHERE id = '00000000-0000-0000-0000-000000000309';

UPDATE scripts SET system_prompt = 'Target organization uses SAP Treasury Management for wire transfers. Dual authorization required for amounts over $10,000 — initiator plus approver via DocuSign. Wire templates are stored in the banking portal. Board-level transactions are handled under NDA. Executive assistants can initiate but not approve wires.'
WHERE id = '00000000-0000-0000-0000-000000000310';

-- Campaign 2: HR (311-315)
UPDATE scripts SET system_prompt = 'Target organization uses Workday for benefits administration and open enrollment. Employee SSNs are stored in Workday with masked display (last 4 only visible to HR admins). Benefits carrier is United Healthcare with enrollment managed through Benefitfocus portal. Open enrollment runs November 1-15 annually.'
WHERE id = '00000000-0000-0000-0000-000000000311';

UPDATE scripts SET system_prompt = 'Target organization uses ADP Workforce Now for payroll processing. Payroll admin access requires separate credentials from corporate SSO. Payroll runs bi-weekly on Fridays with a Wednesday cutoff. System migrations require IT change management approval and a 2-week notice period. Payroll data includes bank accounts for 200+ employees.'
WHERE id = '00000000-0000-0000-0000-000000000312';

UPDATE scripts SET system_prompt = 'Target organization uses Workday for employee records including home addresses. Employee recognition programs are managed through Bonusly platform. Physical award shipments are handled by the office manager. Home addresses are PII-classified and require manager approval to share externally.'
WHERE id = '00000000-0000-0000-0000-000000000313';

UPDATE scripts SET system_prompt = 'Target organization uses Workday as the HRIS with admin access restricted to 3 HR staff. Authentication is through Okta SSO with MFA. HRIS contains PII for all employees (SSN, DOB, salary, bank info). State privacy laws require breach notification within 72 hours. Last security audit was 6 months ago.'
WHERE id = '00000000-0000-0000-0000-000000000314';

UPDATE scripts SET system_prompt = 'Target organization stores personnel files in Workday with SSN access restricted to HR directors and above. Background checks are conducted through Sterling with results stored in a secure SharePoint folder. Legal department must authorize any SSN disclosure outside HR. Board-level personnel reviews happen quarterly.'
WHERE id = '00000000-0000-0000-0000-000000000315';

-- Campaign 3: Marketing (316-320)
UPDATE scripts SET system_prompt = 'Target organization uses Coupa for procurement and expense management. Department budget codes are 10-character alphanumeric strings used for cost center tracking. Sponsorship payments are processed through accounts payable with PO numbers. Marketing has an annual event budget managed in Anaplan.'
WHERE id = '00000000-0000-0000-0000-000000000316';

UPDATE scripts SET system_prompt = 'Target organization works with external creative and media agencies on annual retainer contracts. Tax ID (EIN) is used on W-9 forms and vendor onboarding. Contract renewals are managed through DocuSign with legal review. Marketing uses HubSpot for campaign management and agency collaboration.'
WHERE id = '00000000-0000-0000-0000-000000000317';

UPDATE scripts SET system_prompt = 'Target organization uses Google Analytics 4 and HubSpot for marketing analytics. Platform credentials are managed through Okta SSO but some legacy tools still use direct login. Marketing team has admin access to social media accounts, ad platforms (Google Ads, Meta Business), and the company website CMS.'
WHERE id = '00000000-0000-0000-0000-000000000318';

UPDATE scripts SET system_prompt = 'Target organization runs WordPress CMS with WP Engine hosting. CMS admin credentials are separate from corporate SSO. The website handles lead capture forms and customer-facing content. XSS vulnerabilities would expose visitor data. Website changes require staging deployment before production push.'
WHERE id = '00000000-0000-0000-0000-000000000319';

UPDATE scripts SET system_prompt = 'Target organization uses Coupa for procurement with tiered approval workflows. Procurement codes are required for any purchase over $500. Budget reallocations between cost centers require finance controller approval. Marketing operates on a quarterly budget cycle with mid-quarter reallocation windows.'
WHERE id = '00000000-0000-0000-0000-000000000320';

-- Campaign 4: Engineering (321-325)
UPDATE scripts SET system_prompt = 'Target organization tracks hardware assets in ServiceNow ITAM module. Engineering laptops are leased through Dell Financial Services on 3-year cycles. Asset management portal uses separate credentials from corporate SSO. Equipment insurance claims are filed through the IT procurement team.'
WHERE id = '00000000-0000-0000-0000-000000000321';

UPDATE scripts SET system_prompt = 'Target organization runs production infrastructure on AWS with multi-account setup via AWS Organizations. IAM access keys are used for CI/CD pipelines and developer tooling. API keys are rotated quarterly through HashiCorp Vault. Cloud spend is approximately $50K/month. Resource termination protection is enabled on production accounts.'
WHERE id = '00000000-0000-0000-0000-000000000322';

UPDATE scripts SET system_prompt = 'Target organization uses GitHub Enterprise for source control with SAML SSO through Okta. Engineers have personal GitHub accounts linked to the org. The team attends AWS re:Invent, KubeCon, and internal hackathons. Conference registrations go through the engineering ops team.'
WHERE id = '00000000-0000-0000-0000-000000000323';

UPDATE scripts SET system_prompt = 'Target organization uses Cisco AnyConnect VPN with Active Directory authentication. VPN access is required for production environment access and internal tools. MFA is enforced via Duo Security push. VPN credentials are separate from SSO for network-layer security. Severity 1 incidents trigger mandatory all-hands response within 30 minutes.'
WHERE id = '00000000-0000-0000-0000-000000000324';

UPDATE scripts SET system_prompt = 'Target organization uses GitHub Enterprise with branch protection rules on main. Personal access tokens (PATs) are used for CI/CD integration and API access. Tokens have repo, workflow, and packages scopes. Code reviews require 2 approvals before merge. Repository access is managed through GitHub Teams aligned to engineering squads.'
WHERE id = '00000000-0000-0000-0000-000000000325';

-- Campaign 5: Sales (326-330)
UPDATE scripts SET system_prompt = 'Target organization pays sales commissions monthly through ADP payroll. Commission calculations are tracked in Salesforce CPQ with approval workflows. Direct deposit info is managed through ADP self-service portal. Commission disputes are handled by the sales operations team. Quarterly audits are conducted by external auditors.'
WHERE id = '00000000-0000-0000-0000-000000000326';

UPDATE scripts SET system_prompt = 'Target organization uses Salesforce Enterprise as its CRM with 150+ user licenses. CRM admin access provides full export capabilities for pipeline, customer contacts, and deal data. Authentication is through Okta SSO but admin functions require a separate Salesforce password. Weekly pipeline forecasting meetings rely on live Salesforce dashboards.'
WHERE id = '00000000-0000-0000-0000-000000000327';

UPDATE scripts SET system_prompt = 'Target organization runs an annual President''s Club trip for top sales performers. Past destinations include Cancun and Maui. Travel is booked through Concur with Amex corporate cards. Passport info is collected through a secure HR form for international trips. The sales team has 25+ reps across 3 regions.'
WHERE id = '00000000-0000-0000-0000-000000000328';

UPDATE scripts SET system_prompt = 'Target organization uses Salesforce Enterprise with Shield Platform Encryption for sensitive fields. Customer PII (contacts, billing info, contracts) is stored in Salesforce. Security patches are managed by the Salesforce admin team. Breach notification is required under CCPA for California customer data. Salesforce sessions timeout after 2 hours of inactivity.'
WHERE id = '00000000-0000-0000-0000-000000000329';

UPDATE scripts SET system_prompt = 'Target organization uses Concur for travel and expense management. Travel authorizations over $5,000 require VP approval through Concur workflow. Emergency travel can be booked with post-trip approval. Corporate Amex cards have a $10,000 single-transaction limit. Wire transfers for client entertainment go through accounts payable.'
WHERE id = '00000000-0000-0000-0000-000000000330';
