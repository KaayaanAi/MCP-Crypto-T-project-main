#!/usr/bin/env python3
"""
MCP Crypto Trading Analysis - Setup Validation Script
Validates all components are properly configured and ready for deployment
"""

import sys
import os
import importlib.util
import json
from pathlib import Path

def validate_file_exists(filepath, description):
    """Check if file exists"""
    path = Path(filepath)
    if path.exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def validate_python_syntax(filepath, description):
    """Validate Python file syntax"""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        print(f"✅ {description} syntax valid: {filepath}")
        return True
    except SyntaxError as e:
        print(f"❌ {description} syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    """Run validation checks"""
    print("🚀 MCP Crypto Trading Analysis - Setup Validation")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    all_valid = True
    
    # Core files validation
    core_files = [
        ("mcp_crypto_server.py", "MCP Server"),
        ("crypto_analyzer.py", "Crypto Analyzer"),
        ("binance_client.py", "Binance Client"),
        ("coingecko_client.py", "CoinGecko Client"),
        ("coinmarketcap_client.py", "CoinMarketCap Client"),
        ("technical_indicators.py", "Technical Indicators"),
    ]
    
    print("\n📁 CORE FILES:")
    for filename, description in core_files:
        filepath = base_path / filename
        if validate_file_exists(filepath, description):
            all_valid &= validate_python_syntax(filepath, description)
        else:
            all_valid = False
    
    # Infrastructure files validation
    infra_files = [
        ("infrastructure/database_manager.py", "Database Manager"),
        ("infrastructure/alert_manager.py", "Alert Manager"),
        ("infrastructure/risk_manager.py", "Risk Manager"),
        ("infrastructure/market_scanner.py", "Market Scanner"),
        ("infrastructure/portfolio_tracker.py", "Portfolio Tracker"),
        ("infrastructure/backtester.py", "Backtester"),
    ]
    
    print("\n🏗️ INFRASTRUCTURE FILES:")
    for filename, description in infra_files:
        filepath = base_path / filename
        if validate_file_exists(filepath, description):
            all_valid &= validate_python_syntax(filepath, description)
        else:
            all_valid = False
    
    # Models validation
    model_files = [
        ("models/kaayaan_models.py", "Kaayaan Models"),
        ("legacy/response_models.py", "Response Models"),
    ]
    
    print("\n📋 MODEL FILES:")
    for filename, description in model_files:
        filepath = base_path / filename
        if validate_file_exists(filepath, description):
            all_valid &= validate_python_syntax(filepath, description)
        else:
            all_valid = False
    
    # Docker and deployment files
    deploy_files = [
        ("Dockerfile", "Docker Build File"),
        ("docker-entrypoint.sh", "Docker Entrypoint"),
        ("start_server.sh", "Server Startup Script"),
        ("requirements_mcp.txt", "Python Requirements"),
        (".env.production.example", "Environment Template"),
    ]
    
    print("\n🐳 DEPLOYMENT FILES:")
    for filename, description in deploy_files:
        filepath = base_path / filename
        all_valid &= validate_file_exists(filepath, description)
    
    # Documentation files
    doc_files = [
        ("README.md", "Main Documentation"),
        ("docs/DEPLOYMENT_GUIDE.md", "Deployment Guide"),
        ("docs/API_REFERENCE.md", "API Reference"),
        ("docs/ARCHITECTURE.md", "Architecture Documentation"),
        ("docs/N8N_INTEGRATION.md", "n8n Integration Guide"),
    ]
    
    print("\n📚 DOCUMENTATION:")
    for filename, description in doc_files:
        filepath = base_path / filename
        all_valid &= validate_file_exists(filepath, description)
    
    # Validation summary
    print("\n" + "=" * 60)
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ MCP Crypto Trading Analysis is ready for production deployment")
        print("\nNext Steps:")
        print("1. Review .env.production.example and create .env.production")
        print("2. Run: docker build -t mcp-crypto-trading .")
        print("3. Deploy using docker-compose or Kubernetes")
        print("4. Configure n8n MCP Client node")
        return 0
    else:
        print("❌ VALIDATION FAILED!")
        print("Please fix the issues above before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())