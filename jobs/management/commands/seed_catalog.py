from django.core.management.base import BaseCommand

from jobs.models import Category, TechStack


CATEGORIES = [
    ("web-development", "Web Development"),
    ("mobile-development", "Mobile Development"),
    ("networking-infrastructure", "Networking & Infrastructure"),
    ("data-analytics", "Data & Analytics"),
    ("it-support", "IT Support"),
    ("cybersecurity", "Cybersecurity"),
    ("software-engineering", "Software Engineering"),
    ("ui-ux-design", "UI/UX Design"),
    ("database-administration", "Database Administration"),
    ("other", "Other"),
]

TECH_STACKS = [
    "Angular",
    "C#",
    "C++",
    "Dart",
    "Django",
    "Docker",
    "Figma",
    "Flutter",
    "Git",
    "Java",
    "JavaScript",
    "Kotlin",
    "Laravel",
    "Linux",
    "MongoDB",
    "MySQL",
    "Node.js",
    "PHP",
    "PostgreSQL",
    "Python",
    "React",
    "SQL",
    "Swift",
    "TypeScript",
    "Vue.js",
    "WordPress",
]


class Command(BaseCommand):
    help = "Seed the default job categories and tech stacks."

    def handle(self, *args, **options):
        created_categories = 0
        created_techs = 0

        for slug, name in CATEGORIES:
            _, created = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name},
            )
            if created:
                created_categories += 1

        for name in TECH_STACKS:
            _, created = TechStack.objects.get_or_create(name=name)
            if created:
                created_techs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog seeded. Categories created: {created_categories}, "
                f"tech stacks created: {created_techs}."
            )
        )
