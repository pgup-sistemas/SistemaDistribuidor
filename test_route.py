from app import create_app

app = create_app()

with app.app_context():
    print("All admin_public routes:")
    for rule in app.url_map.iter_rules():
        if 'admin_public' in rule.endpoint:
            print(f'{rule.rule} -> {rule.endpoint}')

    # Check if dashboard route exists
    dashboard_routes = [rule for rule in app.url_map.iter_rules() if rule.endpoint == 'admin_public.admin_dashboard']
    print(f"\nDashboard routes: {len(dashboard_routes)}")
    for rule in dashboard_routes:
        print(f'{rule.rule} -> {rule.endpoint}')