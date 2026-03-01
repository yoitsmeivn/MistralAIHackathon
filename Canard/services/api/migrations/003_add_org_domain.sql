ALTER TABLE organizations ADD COLUMN domain text;
CREATE UNIQUE INDEX idx_organizations_domain ON organizations (domain) WHERE domain IS NOT NULL;
