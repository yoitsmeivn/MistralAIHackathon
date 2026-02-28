create extension if not exists pgcrypto;

create table if not exists participants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null,
    phone text not null,
    team text,
    active boolean not null default true,
    opt_in boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists scenarios (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text not null,
    script_guidelines text not null,
    difficulty text not null default 'medium',
    created_at timestamptz not null default now()
);

create table if not exists campaigns (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    scenario_id uuid not null references scenarios(id),
    created_by text,
    status text not null default 'draft',
    created_at timestamptz not null default now()
);

create table if not exists calls (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references campaigns(id),
    participant_id uuid not null references participants(id),
    scenario_id uuid not null references scenarios(id),
    twilio_call_sid text unique,
    status text not null default 'pending',
    consented boolean not null default false,
    recording_url text,
    started_at timestamptz,
    ended_at timestamptz,
    created_at timestamptz not null default now()
);

create table if not exists turns (
    id uuid primary key default gen_random_uuid(),
    call_id uuid not null references calls(id),
    role text not null check (role in ('user', 'agent')),
    text_redacted text not null,
    text_raw text,
    turn_index integer not null,
    created_at timestamptz not null default now()
);

create table if not exists analysis (
    id uuid primary key default gen_random_uuid(),
    call_id uuid not null unique references calls(id),
    risk_score integer not null check (risk_score >= 0 and risk_score <= 100),
    flags jsonb not null default '[]'::jsonb,
    summary text not null,
    coaching text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_calls_participant_id on calls(participant_id);
create index if not exists idx_calls_status on calls(status);
create index if not exists idx_turns_call_id on turns(call_id);
create index if not exists idx_analysis_call_id on analysis(call_id);
