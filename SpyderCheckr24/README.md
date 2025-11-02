1. `d:\Tools\Argyll_V3.4.1\bin\targen -v -d2 -f24 -G -e0 -B0 front `
2. `d:\Tools\Argyll_V3.4.1\bin\printtarg -v -iSS -r -n -T300 -p4x6 -m0 -a3 front`
3. `type input.txt | d:\Tools\Argyll_V3.4.1\bin\chartread -xl -F6 -Q1964_10 -S front`
4. `go run .`
5. paste calculated values into ti1


then:
1. print
2. scan
3. create icm profile `d:\Tools\Argyll_V3.4.1\bin\colprof -qu -Zr -dpp -v -ax -D"front-uncorrected" -l400 front`
   1. `front.icm`
   2. `front-selphy.icm`
4. invert icm profile `d:\Tools\Argyll_V3.4.1\bin\collink -v -G -ir ..\selphy-cp730\sRGB.icm front.icm front-inv.icm`
5. apply icm profile to the tif
6. print again
7. scan
8. refine with `d:\Tools\Argyll_V3.4.1\bin\refine -v -g ..\selphy-cp730\selphy.icm selphy.icm`
9. verify


Attempt to convert with printer profile created previously:
`d:\Tools\Argyll_V3.4.1\bin\cctiff -v -p -ir -db ..\selphy-cp730\selphy-inv.icm front.tif front-relative.tif`



NOTE: Absolute might help, need to wait for photo paper
Absolute fails - Want 85 0 0, measure 85 -7 5; calibrated measure 85 7 -5!!!


Relative: try include printer linearization: `d:\Tools\Argyll_V3.4.1\bin\colprof -qh -Zr -Zm -dpp -v -cmt -D"spydercheckr front" -M"Selphy cp730" -S ..\selphy-cp730\sRGB.icm -Y c:../selphy-cp730\selphy.cal front`
