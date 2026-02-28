create extension if not exists pgcrypto;

-- Organizations: tenant root
create table if not exists organizations (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null unique,
    industry text,
    plan_tier text not null default 'free',
    max_employees integer,
    max_callers integer,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Users: dashboard admins
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references organizations(id),
    email text not null unique,
    password_hash text not null,
    full_name text not null,
    role text not null default 'viewer',
    is_active boolean not null default true,
    last_login_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Employees: people who receive simulated calls
create table if not exists employees (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references organizations(id),
    full_name text not null,
    email text not null,
    phone text not null,
    department text,
    job_title text,
    risk_level text not null default 'unknown',
    notes text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Callers: fake attacker personas
create table if not exists callers (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references organizations(id),
    created_by uuid references users(id),
    persona_name text not null,
    persona_role text,
    persona_company text,
    voice_profile jsonb not null default '{}'::jsonb,
    phone_number text,
    attack_type text,
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Scripts: reusable attack playbooks
create table if not exists scripts (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references organizations(id),
    created_by uuid references users(id),
    name text not null,
    attack_type text,
    difficulty text not null default 'medium',
    system_prompt text not null,
    objectives jsonb not null default '[]'::jsonb,
    escalation_steps jsonb not null default '[]'::jsonb,
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Campaigns: batch test runs
create table if not exists campaigns (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references organizations(id),
    created_by uuid references users(id),
    name text not null,
    description text,
    attack_vector text,
    status text not null default 'draft',
    scheduled_at timestamptz,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Campaign assignments: caller + script + employee combos
create table if not exists campaign_assignments (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid not null references campaigns(id),
    caller_id uuid not null references callers(id),
    script_id uuid not null references scripts(id),
    employee_id uuid not null references employees(id),
    status text not null default 'pending',
    scheduled_at timestamptz,
    created_at timestamptz not null default now(),
    unique (campaign_id, caller_id, script_id, employee_id)
);

-- Calls: executed phone calls with inline analysis
create table if not exists calls (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references organizations(id),
    campaign_id uuid references campaigns(id),
    assignment_id uuid references campaign_assignments(id),
    caller_id uuid references callers(id),
    script_id uuid references scripts(id),
    employee_id uuid not null references employees(id),
    status text not null default 'pending',
    started_at timestamptz,
    ended_at timestamptz,
    duration_seconds integer,
    phone_from text,
    phone_to text,
    recording_url text,
    transcript text,
    transcript_json jsonb,
    risk_score integer check (risk_score >= 0 and risk_score <= 100),
    employee_compliance text,
    flags jsonb not null default '[]'::jsonb,
    ai_summary text,
    sentiment_analysis jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_employees_org_id on employees(org_id);
create index if not exists idx_callers_org_id on callers(org_id);
create index if not exists idx_scripts_org_id on scripts(org_id);
create index if not exists idx_campaigns_org_id on campaigns(org_id);
create index if not exists idx_campaign_assignments_campaign_id on campaign_assignments(campaign_id);
create index if not exists idx_calls_org_id on calls(org_id);
create index if not exists idx_calls_employee_id on calls(employee_id);
create index if not exists idx_calls_campaign_id on calls(campaign_id);
create index if not exists idx_calls_status on calls(status);
