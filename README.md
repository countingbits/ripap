This is a pretty straight forward script written in python. It will install hostapd and dnsmasq servies and configure the basics for them both. 

You have two choices here to run the script, you can choose to use the setup.sh which is a bash script. This will install python and pip, then prompt you to grab the main repo from here
you can also choose to point it to the apinstall script locally

or you can just grab the apinstall script and directly install it with "py ./apinstall.py" if you already have python 3 installed on your rpi. 


the apinstall will do most of the legwork, including some error handling, but you will have to ensure that your actual netowrk is properly configured


some common issues include
  not having DHCP properly configured on your network, not having DNS properly configured as well. I have tried to address these issues in the script but it often does require you to manually add things to .conf file. 

if you have pihole installed, youll have to manually disable the HDCP on the pi, and enable it in the pihole configuration. same with DNS. upstream dns ends up working a little bit better. 

this can be used in addition to pihole, so you can create a RPI that acts as an access point where all devices connected have their traffic sent through the dns sinkhole, while leaving the rest of your network outside of the sinkhole. 

i noticed while using the sinkhole on my entire network i was having issues casting things from my phone to the TV, so I created this. 

be sure to add permissions to the setup.sh or the apinstall.py prior to attempting to run them.

any issues or anything I have missed please put a request in. 
