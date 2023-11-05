$fn=100;
include <parametric_involute_gear_v5.0.scad>;
include <teardrop.scad>;
include <hub.scad>;

shaftDiameter = 8.3; // the shaft at the center, will be subtracted from the pulley. Better be too small than too wide.
hubDiameter = 28; // if the hub or timing pulley is big enough to fit a nut, this will be embedded.
hubHeight = 8; // the hub is the thick cylinder connected to the pulley to allow a set screw to go through or as a collar for a nut.
flanges = 0; // the rims that keep the belt from going anywhere
hubSetScewDiameter = 3.5; // use either a set screw or nut on a shaft. Set to 0 to not use a set screw.
numSetScrews = 1;


difference(){
  union(){
    translate([0,0,-10-4]) gear (number_of_teeth=8,
      circular_pitch=500,
      gear_thickness = 6,
      rim_thickness = 10+4,
      hub_thickness = 6,
      circles=0);
    hub(hubDiameter,hubHeight,hubSetScewDiameter);
  }
 cylinder(d=6.3, h=50, center=true);
  
};
			


  