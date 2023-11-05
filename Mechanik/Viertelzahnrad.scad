$fn=200;
include <parametric_involute_gear_v5.0_viertel.scad>;
include <teardrop.scad>;
include <hub.scad>;

shaftDiameter = 5; // the shaft at the center, will be subtracted from the pulley. Better be too small than too wide.
hubDiameter = 30; // if the hub or timing pulley is big enough to fit a nut, this will be embedded.
hubHeight = 12; // the hub is the thick cylinder connected to the pulley to allow a set screw to go through or as a collar for a nut.
flanges = 0; // the rims that keep the belt from going anywhere
hubSetScewDiameter = 3; // use either a set screw or nut on a shaft. Set to 0 to not use a set screw.
numSetScrews = 1;


*difference(){
  rotate([0,0,15]) union(){
    difference(){
        translate([0,0,-6]) gear (number_of_teeth=100,
          circular_pitch=500,
          gear_thickness = 6,
          rim_thickness = 6,
          hub_thickness = 6,
          circles=6);
        translate([0,0,-6]) cylinder(h=50, d=hubDiameter, center=T);
    }
    rotate([0,0,-15-90-45]) translate([0,0,-6]) hub(hubDiameter,hubHeight,hubSetScewDiameter);
  }
  *cylinder(d=shaftDiameter, h=50, center=true);
  difference(){
    cube([400,400,20], center=true);
    minkowski(){
      cylinder(d=30, h=20, center=true);
      translate([0,0,-10]) cube([400,400,20]);
    };
  };
  *cube([7.2,7.2,30], center=true);
  rotate([0,0,45/2]) cylinder(d = 8, h=50, $fn=8, center = true);
};
			
*#translate([122,-8,5]) cube([25,14, 10], center=true);
#translate([-8,122,5]) cube([14,25, 10], center=true);