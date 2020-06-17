# coding: utf-8

from django.contrib.auth.hashers import PBKDF2PasswordHasher

class PBKDF2PasswordHasher150KIterations(PBKDF2PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses 150,000 iterations, which is
    the new default in Django 2.2. Using this avoids the following scenario:
    1. KPI inserts a password hash for user Keita into our database, calculated
        with 150,000 iterations;
    2. Keita authenticates directly to KoBoCAT using HTTP Basic;
    3. KoBoCAT's Django 1.8 sees that the number of iterations used by the hash
        in the database differs from what it prefers:
        https://github.com/django/django/blob/6a0dc2176f4ebf907e124d433411e52bba39a28e/django/contrib/auth/hashers.py#L278-L280
    4. KoBoCAT hashes the plain-text password using only 20,000 iterations,
    5. KoBoCAT calls `save()` on the user to update the password hash;
    6. All of Keita's sessions are invalidated.

    Further reading: https://github.com/kobotoolbox/kobocat/issues/612

    This class essentially just copies an example from the documentation:
    https://docs.djangoproject.com/en/1.8/topics/auth/passwords/#increasing-the-work-factor
    """
    iterations = 150000
