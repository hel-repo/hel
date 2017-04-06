#!/bin/bash
set -x  # Show the output for debug

if [ $TRAVIS_BRANCH == 'master' ] ; then
    # Push this repo to `production` machine
    git remote add deploy "travis@fomalhaut.me:/home/totoro/fomalhaut/api/hel"
    git config user.name "Travis CI"
    git config user.email "murky.owl@gmail.com"

    git add .
    git commit -m "Deploy"
    git push --force deploy master
else
    echo "Not deploying, since this branch isn't master."
fi
