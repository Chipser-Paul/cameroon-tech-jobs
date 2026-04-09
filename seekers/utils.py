def calculate_profile_completion(seeker):
    """
    Calculate profile completion percentage for a seeker.
    Returns tuple: (percentage, missing_fields, is_complete)
    """
    total_fields = 10
    completed_fields = 0

    missing = []

    # Check each important field
    if seeker.full_name:
        completed_fields += 1
    else:
        missing.append('Full Name')

    if seeker.email:
        completed_fields += 1
    else:
        missing.append('Email')

    if seeker.phone:
        completed_fields += 1
    else:
        missing.append('Phone Number')

    if seeker.profile_photo:
        completed_fields += 1
    else:
        missing.append('Profile Photo')

    if seeker.bio and len(seeker.bio.strip()) > 20:
        completed_fields += 1
    else:
        missing.append('Bio (min 20 chars)')

    if seeker.experience_level:
        completed_fields += 1
    else:
        missing.append('Experience Level')

    if seeker.skills.exists():
        completed_fields += 1
    else:
        missing.append('Skills')

    if seeker.location:
        completed_fields += 1
    else:
        missing.append('Location')

    if seeker.preferred_categories.exists():
        completed_fields += 1
    else:
        missing.append('Preferred Categories')

    if seeker.availability:
        completed_fields += 1
    else:
        missing.append('Availability')

    percentage = int((completed_fields / total_fields) * 100)
    is_complete = percentage >= 80

    return {
        'percentage': percentage,
        'completed': completed_fields,
        'total': total_fields,
        'missing': missing,
        'is_complete': is_complete,
    }
