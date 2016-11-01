2.1.0
-----
- Added the /profile route.

2.0.1
-----
- Fixed a bug when version details could contain only some of required fields.

2.0.0
-----
- Change the response of ``Packages:GET``.
- When the user is logged in, don't respond with the ``400 Bad Request`` message if they send some action, other than ``log-out``.
- Packages now can have multiple owners.
- Usernames are checked against a regex (``[A-Za-z0-9-_]+``).

1.0.0
-----
The first stable API release.

- Added ``stats.date`` field.

0.7.2
-----
- Added URL validity checks.

0.7.1
-----
- Removed ``passwd-confirm`` param.

0.7.0
-----
- Made the /auth view process ``application/json`` instead of ``application/x-www-form-urlencoded`` (that was illogical).

0.6.1
-----
- Made the previous change not breaking.

0.6.0
-----
- Add the ``stats.views`` field. *This breaks existing packages*.

0.5.0
-----
- Changed the replacement character. This breaks existing packages.
- Made error messages unified.

0.4.1
-----
- Added ``Access-Control-Allow-Origin`` header for cross-origin AJAX API requests.
- Fixed strange log in and log out behaviours.

0.4.0
-----
- Separated the auth logic from the home view, effectively enabling authorization via API.

0.3.2
-----
- Added versions.num.changes field.

0.3.1
-----
- Minor updates.

0.3.0
-----
- Wrappers for the remaining views.

  - A wrapper around package creating.
  - A User:GET wrapper.
  - A User:POST wrapper.

- 100% test coverage.

0.2.0
-----
- Short description search.
- Disabled use of GET params for authorization.
- Added a teapot.
- Fixed an issue where the forms were shown before loading the page.
- Implementation of package updating (i.e., Package:PUT wrapper).
- Updated package model, breaking many things depending on the old one.

  - Reimplementation of some classes related to search.

- Set up Travis CI.

0.1.0
-----
- Authentication and authorization.
- Added tests.
- Packages:GET, Users:GET wrappers.

0.0.2
-----
- Updated landing design.
- Basic package search.

0.0.1
----
- The beginning of the story.
- Simple /package controller.
