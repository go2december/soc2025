# Generated by Django 5.2.1 on 2025-05-23 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='ชื่อหมวดหมู่')),
                ('slug', models.SlugField(blank=True, max_length=100, null=True, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='คำอธิบายหมวดหมู่')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด')),
            ],
            options={
                'verbose_name': 'หมวดหมู่',
                'verbose_name_plural': 'หมวดหมู่ข่าว',
                'ordering': ['name'],
            },
        ),
    ]
