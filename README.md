# Quadcast2-non-s-control-For-Linux
i wanted to create a gui script that can control lightning on quadcast 2 non s version since its not there on openrgb


U must run this in your terminal to give access to the normal user for quadcast2controller
```$ sudo nano /etc/udev/rules.d/99-quadcast2.rules```
Paste this in it : 
`SUBSYSTEM=="usb", ATTR{idVendor}=="03f0", ATTR{idProduct}=="09af", MODE="0666"`
Then press ctrl+x then y to save it and enter to exit 

sudo ``udevadm control --reload-rules`` to reload rules and then ``sudo udevadm trigger`` to apply 

to make sure ur id is the one i have use `lsusb` its called HP, Inc HyperX QuadCast 2 Controller also to see the device number

to check it after use this ````ls -l /dev/bus/usb/001/"your device number"```` it should show crw-rw-rw- 

after that download the appimage and it should run u can use gear lever to add it to the app menu or whatever works 

also it already working on the preset that i personally like u can change it 

however it requires some dependencies i use fedora so here is how to install it if i didn't manage to bundle it with the appimage ``sudo dnf install python3 qt6-qtbase qt6-qtsvg qt6-qtbase-devel pyusb``

<img width="492" height="425" alt="image" src="https://github.com/user-attachments/assets/6d957052-1706-4429-93e1-e3dc20ff78e0" />

if anyone wants to see how does it look

