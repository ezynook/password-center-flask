#!/bin/bash

TODAY=$(date)

git add .
git commit -m "$TODAY"
git  push origin main