#!/bin/bash
set -x  # Show the output for debug

# Get encryption key
openssl aes-256-cbc -K $encrypted_0be4e10375ea_key -iv $encrypted_0be4e10375ea_iv -in deploy-key.enc -out deploy-key -d
rm deploy-key.enc
chmod 600 deploy-key
mv deploy-key ~/.ssh/id_rsa
