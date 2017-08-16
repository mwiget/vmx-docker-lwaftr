#!/bin/bash
CONTAINER=$1
TIMESTAMP="$(date '+%Y%m%d-%H%M')"
if [ -z "$CONTAINER" ]; then
  echo "running container name required"
  exit 1
fi
echo "collecting data in container $CONTAINER ..."
docker exec -ti $CONTAINER bash -c "cd /tmp; (ps axw && lscpu && cat /proc/meminfo && /show_affinity.sh) > sysinfo.txt; tar zcf /tmp/support-info.tgz /VERSION *.log mac_* pci_* *txt *txt.s *.cfg *.conf config.* test*.sh ../config_drive/vmm-config.tgz ../root/.bashrc /usr/local/bin/snabb" 
echo "transferring data from the container to host ..."
docker cp $CONTAINER:/tmp/support-info.tgz support-info-$TIMESTAMP.tgz
ls -l support-info-$TIMESTAMP.tgz
