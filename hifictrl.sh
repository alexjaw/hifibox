#!/usr/bin/env bash
ACTION=$1
INPUT=$2

STATE=0
if [ $ACTION = "on" ]; then
    $STATE=1
    echo "Observe, turning HiFiBox requires restart of the box."
    # All this is now performed by the mcu during init
    # MCU also configures the dsp and the dac
    #echo "pwr_enable"
    #./hifi.py -c "io set pwr_enable 1"
    #echo "adc_dac_dsp_reset_neg"
    #./hifi.py -c "io set adc_dac_dsp_reset_neg 1"
    #echo "out_enable"
    #./hifi.py -c "io set out_enable 1"
elif [ $ACTION = "off" ]; then
    $STATE=0
    echo "Turning HiFiBox" $ACTION
    echo "out_enable"
    ./hifi.py -c "io set out_enable 0"
    echo "adc_dac_dsp_reset_neg"
    ./hifi.py -c "io set adc_dac_dsp_reset_neg 0"
    echo "pwr_enable"
    ./hifi.py -c "io set pwr_enable 0"
else
   echo Uhum...
   exit
fi

# Is performed by the mcu during init
#if [ $ACTION = "on" ]; then
#    echo "Activating DAC"
#    i2cset -y 1 0x10 0x00 0x1d
#fi

if [ $ACTION = "on" ]; then
    if [ $INPUT = "toslink" ]; then
        echo "Input:" $INPUT
        ./hifi.py -c "io set toslink_enable 1"
    fi
fi
