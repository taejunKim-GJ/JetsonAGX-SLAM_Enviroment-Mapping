#include "LIVMapper.h"

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions options;
  options.allow_undeclared_parameters(true);
  options.automatically_declare_parameters_from_overrides(true);
  rclcpp::Node::SharedPtr nh;
  image_transport::ImageTransport it_(nh);
  LIVMapper mapper(nh, "laserMapping", options);
  mapper.initializeSubscribersAndPublishers(nh, it_);

  // 1. Run main SLAM loop (Ctrl+C will break this)
  mapper.run(nh);
  
  // 2. This point is reached AFTER rclcpp::ok() becomes false
  std::cout << "\n[ Main ] SLAM stopped. Executing heavy post-processing tasks..." << std::endl;
  std::cout << "[ Main ] This may take more than 10 seconds. Do not force kill!" << std::endl;
  
  // 3. Call save and refinement explicitly outside the ROS loop
  mapper.savePCD();
  
  std::cout << "[ Main ] All tasks completed. System exiting safely." << std::endl;
  
  rclcpp::shutdown();
  return 0;
}
