cd /work/users/trondk/KINO/Postpro
./ncfile_subsetting.sh 1948 01 01 kino_1600m_z.nc time d
for (( yy=2011; yy<=2013; yy++ )); do
for mm in 01 02 03 04 05 06 07 08 09 10 11 12; do
ncrcat -O kino_1600m_z.nc_${yy}${mm}* kino_1600m_z.nc_${yy}${mm}
cdo timmean kino_1600m_z.nc_${yy}${mm} kino_1600m_z_mean.nc_${yy}${mm}
rm kino_1600m_z.nc_${yy}${mm}
echo “Finished with year $yy and month $mm”
done
done
rm kino_1600m_z.nc_${yy}${mm}????