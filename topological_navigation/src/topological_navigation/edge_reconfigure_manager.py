#!/usr/bin/env python
"""
Created on Wed Feb 10 15:58:34 2021

@author: Adam Binch (abinch@sagarobotics.com)
"""
#############################################################################################################
import rospy, dynamic_reconfigure.client
from strands_navigation_msgs.srv import ReconfAtEdges


class EdgeReconfigureManager(object):
    
    
    def __init__(self):
        
        rospy.logwarn("Edge Reconfigure Manager: USING EDGE RECONFIGURE ...")
        
        self.edge = {}
        self.default_config = {}
        self.namespaces = []
        
        self.current_edge_group = "none"
        self.edge_groups = rospy.get_param("/edge_nav_reconfig_groups", {})
        
        
    def register_edge(self, edge):
        
        self.edge = edge
        
        namespaces = []
        if "config" in edge:
            namespaces = [param["namespace"] for param in edge["config"]]
            
        self.namespaces = list(set(namespaces))
        if self.namespaces:
            rospy.loginfo("Edge Reconfigure Manager: Processing edge {} ...".format(edge["edge_id"]))
        
        
    def initialise(self):
        
        self.initial_config = {}                    
        for namespace in self.namespaces:
            rospy.loginfo("Edge Reconfigure Manager: Getting initial configuration for {}".format(namespace))
            
            client = dynamic_reconfigure.client.Client(namespace, timeout=2.0)
            try:
                self.initial_config[namespace] = client.get_configuration()
                
            except rospy.ServiceException as e:
                rospy.warn("Edge Reconfigure Manager: Caught service exception: {}".format(e))
        
        self.initial_params = []        
        if "config" in self.edge:
            for param in self.edge["config"]:
                if param["namespace"] in self.initial_config:
                    value = self.initial_config[param["namespace"]][param["name"]]
                    self.initial_params.append({"namespace":param["namespace"], "name":param["name"], "value":value})
                
        
    def reconfigure(self):
        """
        If using the new map then edge reconfigure is done using settings in the map.
        """
        if "config" in self.edge:
            for param in self.edge["config"]:
                if param["namespace"] in self.initial_config:
                    rospy.loginfo("Edge Reconfigure Manager: Setting {} = {}".format("/".join((param["namespace"], param["name"])), param["value"]))                    
                    self.update(param["namespace"], {param["name"]: param["value"]})
                    
                    
    def _reset(self):
        """
        Used to reset edge params to their default values when the action has completed (only if using the new map)
        """
        for param in self.initial_params:
            rospy.loginfo("Edge Reconfigure Manager: Resetting {} = {}".format("/".join((param["namespace"], param["name"])), param["value"]))                    
            self.update(param["namespace"], {param["name"]: param["value"]})
                
                
    def update(self, namespace, params):
        
        client = dynamic_reconfigure.client.Client(namespace, timeout=2.0)
        try:
            client.update_configuration(params)
            
        except rospy.ServiceException as e:
            rospy.logwarn("Edge Reconfigure Manager: Caught service exception: {}".format(e))
                    
                    
    def srv_reconfigure(self, edge_id):
        """
        If using the old map then edge reconfigure is done via a service.
        """
        edge_group = "none"
        for group in self.edge_groups:
            print "Check Edge: ", edge_id, "in ", group
            if edge_id in self.edge_groups[group]["edges"]:
                edge_group = group
                break

        print "current group: ", self.current_edge_group
        print "edge group: ", edge_group

        if edge_group is not self.current_edge_group:
            print "RECONFIGURING EDGE: ", edge_id
            print "TO ", edge_group
            try:
                rospy.wait_for_service("reconf_at_edges", timeout=3)
                reconf_at_edges = rospy.ServiceProxy("reconf_at_edges", ReconfAtEdges)
                resp1 = reconf_at_edges(edge_id)
                print resp1.success
                if resp1.success:
                    self.current_edge_group = edge_group
            except rospy.ServiceException, e:
                rospy.logerr("Service call failed: %s" % e)
        print "-------"
############################################################################################################# 