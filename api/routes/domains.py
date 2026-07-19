"""Domain config API routes.

GET /v1/domains              -> list domains
GET /v1/domains/{name}       -> domain config + rules
"""
from fastapi import APIRouter, HTTPException
from core import domain_config

router = APIRouter(prefix="/v1/domains", tags=["domains"])

@router.get("")
def list_domains():
    return {"items": domain_config.list_domains()}

@router.get("/{domain}")
def get_domain(domain: str):
    if domain not in domain_config.list_domains():
        raise HTTPException(404, f"Domain not found: {domain}")
    rules = domain_config.get_rules(domain)
    config = {}
    for key in ("config.default_currency", "config.risk_threshold", "config.auto_respond", "config.monitoring_cron"):
        config[key.split(".", 1)[1]] = domain_config.get_config(domain, key)
    return {"domain": domain, "rules": rules, "config": config, "rule_count": len(rules)}
