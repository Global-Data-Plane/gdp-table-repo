#!/bin/bash
docker run -v /mnt/c/Users/rick/OneDrive/Projects/Tetratech/gdp-table-repo/.keys/ultisim-18196618aeb0.json:/tmp/.keys/ultisim-18196618aeb0.json -p 5000:5000 --env-file .env-docker $1