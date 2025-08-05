from django.core.management.base import BaseCommand
from quotes.models import AboutContent

class Command(BaseCommand):
    help = 'Create initial about content'

    def handle(self, *args, **options):
        # Check if about content already exists
        if AboutContent.objects.filter(is_active=True).exists():
            self.stdout.write(
                self.style.WARNING('About content already exists. Skipping creation.')
            )
            return

        # Create initial about content
        about_content = AboutContent.objects.create(
            title='About Us',
            subtitle='ABOUT COMPANY',
            content='''
<p><strong>The CleanHandy</strong> was founded in 2025 with a clear mission: to make everyday life easier through dependable, professional, and high-quality cleaning and handyman services. Although the brand is young, our team brings over a decade of hands-on industry experience to every job we take on.</p>

<p>We pride ourselves on combining modern tools and eco-friendly products with a passion for precision and reliability. Whether you need help transforming your space, maintaining it, or preparing it for something new — CleanHandy is the name you can trust.</p>

<p><strong>Why choose CleanHandy?</strong></p>
<div class="rewards-left-list">
<ul>
    <li><i class="fa-sharp fa-light fa-circle-check"></i> Founded in 2025 with a professional team behind it</li>
    <li><i class="fa-sharp fa-light fa-circle-check"></i> Over 12 years of combined industry experience</li>
    <li><i class="fa-sharp fa-light fa-circle-check"></i> Fully insured, trained, and background-checked professionals</li>
    <li><i class="fa-sharp fa-light fa-circle-check"></i> Safe, sustainable, and effective cleaning solutions</li>
    <li><i class="fa-sharp fa-light fa-circle-check"></i> Honest pricing and customizable service plans</li>
    <li><i class="fa-sharp fa-light fa-circle-check"></i> Responsive support and 100% satisfaction guarantee</li>
</ul>
</div>

<p>Whether you're managing a home, a rental property, or a business, our skilled technicians are ready to help. At CleanHandy, we take care of the chores and fixes — so you can enjoy peace of mind and more free time.</p>
            ''',
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created about content: {about_content}')
        ) 