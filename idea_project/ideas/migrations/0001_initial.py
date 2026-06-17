import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InvestorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('tag', models.CharField(choices=[('Technology', 'Technology'), ('Health', 'Health'), ('Finance', 'Finance'), ('Education', 'Education'), ('Environment', 'Environment'), ('Marketing', 'Marketing'), ('Startups', 'Startups'), ('Sustainability', 'Sustainability'), ('AI', 'AI'), ('Blockchain', 'Blockchain'), ('E-commerce', 'E-commerce'), ('Social Media', 'Social Media'), ('Cybersecurity', 'Cybersecurity'), ('Robotics', 'Robotics'), ('Fintech', 'Fintech'), ('Legal Tech', 'Legal Tech'), ('Gaming', 'Gaming'), ('Augmented Reality', 'Augmented Reality'), ('Virtual Reality', 'Virtual Reality'), ('Travel', 'Travel'), ('Real Estate', 'Real Estate'), ('Food & Beverage', 'Food & Beverage'), ('Telecommunications', 'Telecommunications')], default='', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SignupDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('category', models.CharField(choices=[('entrepreneur', 'Entrepreneur'), ('investor', 'Investor')], max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='VideoResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('video_file', models.FileField(blank=True, null=True, upload_to='videos/')),
                ('video_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='ideas.signupdetail')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='ideas.signupdetail')),
            ],
        ),
        migrations.CreateModel(
            name='Idea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('tag', models.CharField(choices=[('Technology', 'Technology'), ('Health', 'Health'), ('Finance', 'Finance'), ('Education', 'Education'), ('Environment', 'Environment'), ('Marketing', 'Marketing'), ('Startups', 'Startups'), ('Sustainability', 'Sustainability'), ('AI', 'AI'), ('Blockchain', 'Blockchain'), ('E-commerce', 'E-commerce'), ('Social Media', 'Social Media'), ('Cybersecurity', 'Cybersecurity'), ('Robotics', 'Robotics'), ('Fintech', 'Fintech'), ('Legal Tech', 'Legal Tech'), ('Gaming', 'Gaming'), ('Augmented Reality', 'Augmented Reality'), ('Virtual Reality', 'Virtual Reality'), ('Travel', 'Travel'), ('Real Estate', 'Real Estate'), ('Food & Beverage', 'Food & Beverage'), ('Telecommunications', 'Telecommunications')], max_length=50)),
                ('entrepreneur', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='ideas', to='ideas.signupdetail')),
            ],
        ),
    ]
