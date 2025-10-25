from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class CleanHandyAdminSite(AdminSite):
    """Custom admin site for CleanHandy with better organization"""
    
    # Change main title from "QUOTES" to "Administration"
    site_header = "CleanHandy Administration"
    site_title = "CleanHandy Admin"
    index_title = "Welcome to CleanHandy Administration"
    
    # Set site URL for better navigation
    site_url = "/"
    
    # Override app names to be more user-friendly
    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site, putting the main app first and renaming it.
        """
        app_list = super().get_app_list(request)
        
        # Define the order we want apps to appear
        app_order = [
            'quotes',  # Main app first
            'accounts',
            'adminpanel',
            'blog',
            'bookings',
            'customers',
            'giftcards',
            'auth',
            'sites',
        ]
        
        # Sort the app list based on our custom order
        def get_app_order(app):
            try:
                return app_order.index(app['app_label'])
            except ValueError:
                return len(app_order)  # Put unknown apps at the end
        
        app_list.sort(key=get_app_order)
        
        # Rename the quotes app to "Administration"
        for app in app_list:
            if app['app_label'] == 'quotes':
                app['name'] = 'Administration'
                app['verbose_name'] = 'Administration'
                break
        
        return app_list

# Create the custom admin site instance
admin_site = CleanHandyAdminSite(name='cleanhandy_admin')

# You can use this custom admin site by replacing admin.site with admin_site
# in your urls.py if you want to completely customize the admin
