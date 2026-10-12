# LinkedIn Post Draft and Projects Section

> Every statement below matches the repository's recorded results (185 pytest tests passed on the author's machine on 12 Oct 2026). Edit freely, but do not add tools or results that are not in the repository.

## Post (about 150 words)
I recently built **ShopEase**, a small fictional e-commerce app, to practise hands-on QA and basic web application security testing.

What's in the repo:
- Test plan, scenarios and 24 detailed manual test cases (boundary value analysis and equivalence partitioning)
- A pytest + requests API suite (185 tests, all passing in my latest run) and a Postman collection covering authentication, authorization, validation and error handling
- SQL queries to verify registrations, order ownership and order totals
- A local-only security checklist (access control, session behaviour, price tampering, input handling)

What I learned: testing found two real low-severity issues, both fixed and documented with regression tests: the server banner revealed framework versions, and very large IDs caused HTTP 500 errors instead of 404. I also kept results honest: manual browser cases and the Postman run are still marked Not Run until I execute them.

This is a learning project on my own local environment, not client work or a certified penetration test. Feedback welcome!

Repo: <link>

#SoftwareTesting #QA #APITesting #Pytest #Postman #CyberSecurity #LearningInPublic

## Add to LinkedIn "Projects"
1. Open your profile > **Add profile section** > **Additional** (or **Recommended**) > **Add projects**. (Menus change; look for "Projects".)
2. **Project name:** ShopEase: E-commerce QA, API Testing & Security Validation
3. **Description:** Local educational project: manual test design, pytest/Postman API testing, SQL validation and basic security checks on a fictional Flask app. Not a certified audit.
4. **Project URL:** your GitHub repository link. Add dates and skills (Software Testing, API Testing, Pytest, Postman, SQL, Web Application Security Basics).
5. Save, then publish the post and link to it in your "Featured" section if you like.
