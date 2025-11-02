## Read with proper illuminant
`type selphy.txt | d:\Tools\Argyll_V3.4.1\bin\chartread -xl -F6 -Q1964_10 -S selphy`


## This initially was used to print targets
`d:\Tools\Argyll_V3.4.1\bin\colprof -qh -Zr -dpp -v -D"Selphy CP730" selphy`

## this produces better gamut (handles yellow paper properly)
`d:\Tools\Argyll_V3.4.1\bin\colprof -qh -Za -Zm -dpp -v -cmt -D"Selphy CP730" -S sRGB.icm selphy`

## Correction profile!!!

Inverse mapping
`d:\Tools\Argyll_V3.4.1\bin\collink -v -G -ir sRGB.icm selphy-m.icm selphy-inv.icm`

NOTE: colprof above generates a forward profile. we want inverse profile.
forward profile is good for softproof.
inverse is good for corrections.

## generate corrected target
`d:\Tools\Argyll_V3.4.1\bin\cctiff -v -p -ir -db selphy.icm selphy.tif selphy-corrected.tif`



Absolute failed. Relative best. Perception intent looks best so far.