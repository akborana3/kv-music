# PragyanMusic/utils/user.py

def get_username(user):
    """
    Returns the first name of the user unless the user is anonymous,
    in which case it returns 'Anonymous'.
    """
    return user.first_name if not getattr(user, 'is_anonymous', False) else "Anonymous"
