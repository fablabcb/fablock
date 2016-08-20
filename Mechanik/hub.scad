module hub(hubDiameter,hubHeight,hubSetScewDiameter)
	{
		if(hubSetScewDiameter == 0)
		{
			cylinder(h = hubHeight, r = hubDiameter/2, center =false);
		}
		if(hubSetScewDiameter >= 0)
		{
			difference()
			{
				
				cylinder(h = hubHeight, r = hubDiameter/2, center =false);
				for(rotZ=[1:numSetScrews])
					rotate([0,0,360*(rotZ/numSetScrews)]) translate([0,0,hubHeight/2]) rotate([0,90,0]) union(){
						translate([0,0,hubDiameter/4]) teardrop(hubSetScewDiameter/2, hubDiameter/2+1,true);
						translate([-1,0,hubDiameter*9/32]) cube(size=[hubHeight/2+1+3.5,5.9,2.5],center=true);
					}
			}
		}
	};