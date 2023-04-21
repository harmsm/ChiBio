#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

INSTALL_DIR=/root/chibio

#cd /etc/ssh/
#echo "PermitRootLogin yes" >> sshd_config

#echo -e "root\nroot" | passwd root
#sed -i 's@-w /var/lib/cloud9@-w /root/chibio@' /lib/systemd/system/cloud9.service
#sed -i 's@1000@root@' /lib/systemd/system/cloud9.service
#sed -i 's@User=debian@User=root@' /lib/systemd/system/cloud9.service

sudo apt-get update

mkdir ${INSTALL_DIR}
cp cb.sh ${INSTALL_DIR}
cp app.py ${INSTALL_DIR}
cp static -r ${INSTALL_DIR}
cp templates -r ${INSTALL_DIR}
cp configure_network.sh ${INSTALL_DIR}
cp config.json ${INSTALL_DIR}

pip3 install Gunicorn
pip3 install flask
pip3 install serial
pip3 install Adafruit_GPIO
pip3 install --user --upgrade setuptools
pip3 install simplejson
pip3 install smbus2
pip3 install numpy

tar xvzf Adafruit_BBIO-1.2.0.tar.gz
cd Adafruit_BBIO-1.2.0/
sed -i "s/'-Werror', //g" setup.py
python setup.py install

cd ${INSTALL_DIR}
chmod +x cb.sh

if [[ ! -e "/etc/rc.local" ]]; then
    sudo echo "#!/bin/bash" > /etc/rc.local
    sudo echo "" >> /etc/rc.local
    sudo chmod 755 /etc/rc.local
fi

#reboot now
