# dataTypes.py
# dataType objects for DORA.

# imports.
import random, pdb

# set parameters.

# Token units
# noinspection PyPep8Naming
class TokenUnit(object):
    def __init__(self, my_name, my_set, analog, inferred_now, myanalog):
        self.name = my_name
        self.set = my_set # driver, recipient, newSet, or memory.
        self.myanalog = myanalog # connection to the analog object I belong to (all tokens from the same analog connect to the same analog object).
        self.act = 0.0
        self.max_act = 0.0
        self.my_index = None
        self.inhibitor_input = 0.0
        self.inhibitor_act = 0.0
        self.mappingHypotheses = [] # will house links to my mapping hypotheses.
        self.mappingConnections = [] # will house links to my mapping connections.
        self.max_map_unit = None # unit to which I most map.
        self.max_map = 0.0 # my largest mapping connection.
        self.td_input = 0.0
        self.bu_input = 0.0
        self.lateral_input = 0.0
        self.map_input = 0.0
        self.net_input = 0.0
        self.GUI_unit = None # GUI_Node unit to which I connect.
        self.my_made_unit = None # unit in the new set I have caused to be inferred.
        self.my_maker_unit = None # unit that made me (if I've been inferred in the newSet).
        self.inferred = inferred_now # have I just been inferred (then True) or am I user made or already a part of memory (then False)?
        self.retrieved = False
        self.copy_for_DR = False # have I been copied into the driver/recipient?
        self.copied_DR_index = None # what is the index of my copied unit in MEMORY (if I have been copied over; None, otherwise).
        self.sim_made = inferred_now # have I been created during a simulation. This flag takes the same value as inferred_now, but does not get reset when the new unit leaves newSet. For use in interpretting large batch sims (e.g., check all units made during simulation vs. those created by user).
    
    def initialize_input(self, refresh): # initialize inputs to 0, and td_input to refresh.
        self.td_input = refresh
        self.bu_input = 0.0
        self.lateral_input = 0.0
        self.map_input = 0.0
        self.net_input = 0.0
    
    def initialize_act(self):
        self.initialize_input(0.0)
        self.act = 0.0 # initialize act to 0.0.
    
    def initialize_state(self):
        self.initialize_act(0.0)
        self.retrieved = False
    
    def update_act(self, gamma, delta, HebbBias):
        self.net_input = self.td_input + self.bu_input + self.lateral_input + (self.map_input * HebbBias)
        delta_act = gamma * self.net_input * (1.1 - self.act) - (delta*self.act)
        self.act += delta_act
        # hard limit activation to between 0.0 and 1.0.
        if self.act > 1.0:
            self.act = 1.0
        if self.act < 0.0:
            self.act = 0.0
    
    def zero_laternal_input(self): # set lateral_input to 0 (to allow synchrony at different levels by 0-ing lateral inhibition at that level (e.g., to bind via synchrony, 0 lateral inhibition in POs).
        self.lateral_input = 0
    
    def update_inhibitor_input(self): # update the input to my inhibitor by my current activation.
        self.inhibitor_input += self.act
    
    def reset_inhibitor(self): # reset the inhibitor_input and act to 0.0.
        self.inhibitor_input = 0.0
        self.inhibitor_act = 0.0


class Groups(TokenUnit):
    def __init__(self, my_name, analog, inferred_now, myanalog, myGroupLayer):
        TokenUnit.__init__(self, my_name, my_set, analog, inferred_now, myanalog) # default init for all tokens.
        self.my_type = 'Group'
        self.myGroupLayer = myGroupLayer # the group layer I am at. If I take Ps as children, then I am at level 1, otherwise, I am at level of my child Groups + 1.
        self.myParentGroups = [] # connections to Groups above me. Initialized to empty.
        self.myChildGroups = [] # connections to Groups below me. Initialized to empty.
        self.myPs = [] # Ps to which I am connected. Initialized to empty.
        self.myRBs = [] # RBs to which I am connected. Initialized to empty. For Groups talking single-place pred structures as arguments.
        self.mySemantics = [] # Links to my semantic units: Inialized to empty.
        self.inhibitorThreshold = 'NA' ######### NOTE: THIS MIGHT NEED TO BE CHANGED LATER.
    
    def get_index(self, memory):
        self.my_index = memory.Groups.index(self)
    
    def update_inhibitor_act(self):
        if self.inhibitor_input >= self.inhibitorThreshold:
            self.inhibitor_act = 1
    
    def update_input_driver(self, memory, asDORA):
        # sources of input:
        # Exitatory: td (Groups above me), bu (my Ps or Groups below me).
        # Inhibitory: lateral (other Group units in same layer as me*3), inhibitor.
        pass
    
    def update_input_recipient(self, memory, asDORA, phase_set, lateral_input_level):
        # sources of input:
        # Exitatory: td (Groups above me), bu (my Ps or Groups below me, my semantics), mapping input.
        # Inhibitory: lateral (other Group units in same layer as me*3), inhibitor.
        pass


class PUnit(TokenUnit):
    def __init__(self, my_name, my_set, analog, inferred_now, myanalog):
        TokenUnit.__init__(self, my_name, my_set, analog, inferred_now, myanalog) # default init for all tokens.
        self.my_type = 'P'
        self.myRBs = [] # connections to my RBs: Initialized to empty.
        self.myParentRBs = [] # RBs to which I am an argument: Initialized to empty.
        self.myGroups = [] # Groups I am a part of: initialized to empty.
        self.mode = 0 # as default mode is neutral.
        self.inhibitorThreshold = 440 ######### NOTE: THIS MIGHT NEED TO BE CHANGED LATER.
    
    def get_index(self, memory):
        self.my_index = memory.Ps.index(self)
    
    def initialize_Pmode(self): # initialize my mode back to neutral.
        self.mode = 0
    
    def get_Pmode(self): # set my P mode.
        # set Pmode to 1 (Parent) if input from my RBs below me is greater than input from RBs above me, set Pmode to -1 (child) if input from RBs above me is greater than input from RBs below me, and set Pmode to 0 (neutral) otherwise.
        # get the input from RBs below me (.myRBs) and RBs above me (.myParentRBs).
        parent_input = 0
        child_input = 0
        for myRB in self.myRBs:
            parent_input += myRB.act
        for myParentRB in self.myParentRBs:
            child_input += myParentRB.act
        if parent_input > child_input:
            self.mode = 1
        elif parent_input < child_input:
            self.mode = -1
        else:
            self.mode = 0
    
    def update_inhibitor_act(self):
        if self.inhibitor_input >= self.inhibitorThreshold:
            self.inhibitor_act = 1
    
    def update_input_driver_parent(self, memory, asDORA):
        # P units in parent mode:
        # sources of input:
        # Exitatory: td (my Groups), bu (my RBs).
        # Inhibitory: lateral (other P units in parent mode*3), inhibitor.
        # get my td_input
        # my td_input comes from my RBs.
        for Group in self.myGroups:
            self.td_input += Group.act
        # get my bu_input
        # my bu_input comes from my RBs.
        for myRB in self.myRBs:
            self.bu_input += myRB.act
        # get my lateral_input (comes from other Ps in parent mode).
        for myP in memory.driver.Ps:
            # if the P is in parent and is not me, then add inhibitory input.
            if myP.mode == 1 and myP is not self:
                self.lateral_input -= myP.act*3
    
    def update_input_driver_child(self, memory, asDORA):
        # P units in child mode:
        # sources of input:
        # Exitatory: td (my parent RBs and my Groups).
        # Inhibitory: lateral (other P units in child mode, and, if in DORA mode, then other POs not connected to same RB and other PO conected to same RB*3), inhibitor.
        # get my td input from my RBs.
        for myRB in self.myParentRBs:
            self.td_input += myRB.act
        # get my td input from my Groups.
        for Group in self.myGroups:
            self.td_input += Group.act
        # get my bu imput from my semantics (not currently implemented).
        # get lateral inhibition from other child P units and other POs not connected to my myRB.
        for myP in memory.driver.Ps:
            if myP.mode == -1 and myP is not self:
                self.lateral_input -= myP.act
        for myPO in memory.driver.POs:
            # to inhibit me, the PO must be an object and if not asDORA that PO is not connected to the same RB as me.
            if myPO.predOrObj == 0: # i.e., if the PO is an object.
                if asDORA:
                    self.lateral_input -= myPO.act
                else:
                    # make sure that the PO is not connected to the same RB as me.
                    # for each RB I am connected to make sure that RB is not in PO's RBs.
                    same_RB = False
                    for myRB in self.myRBs:
                        if myRB in myPO.myRBs:
                            same_RB = True
                            break
                    # if same_RB is false, get inhibition from the myPO.
                    if not same_RB:
                        self.lateral_input -= myPO.act
    
    def update_input_recipient_parent(self, memory, asDORA, phase_set, lateral_input_level):
        # P units in parent mode:
        # sources of input:
        # Exitatory: td (my Groups), bu (my RBs), mapping input.
        # Inhibitory: lateral (other P units in parent mode*3), inhibitor.
        # get my exhitatory input.
        # td from my Groups.
        # td from my RBs, ONLY if in the second phase_set or above.
        # (NOTE: phase_set counts from 0, so phase_set == 1 is the second phase_set.)
        if phase_set >= 1:
            for Group in self.myGroups:
                self.td_input += Group.act
        # bu.
        for myRB in self.myRBs:
            self.bu_input += myRB.act
        # mapping.
        # mapping input is for each similar token unit in the driver, 3*(driver.act*mapping_weight) - max(mapping_weight_driver_unit) - max(own_mapping_weight).
        for mappingConnection in self.mappingConnections:
            self.map_input += (3*mappingConnection.weight*mappingConnection.driverToken.act) - (self.max_map*mappingConnection.driverToken.act) - (mappingConnection.driverToken.max_map*mappingConnection.driverToken.act)
        # get my inhibitory input.
        # lateral.
        # from other P units.
        for myP in memory.recipient.Ps:
            # get inhibition from the P as long as it is in parent and is not me:
            if myP.mode == 1 and myP is not self:
                self.lateral_input -= myP.act*lateral_input_level
        # from my inhibitor.
        self.lateral_input -= self.inhibitor_act*10
    
    def update_input_recipient_child(self, memory, asDORA, phase_set, lateral_input_level):
        # Units in child mode:
        # Units in parent mode:
        # sources of input:
        # Exitatory: td (RBs above me, my Groups), mapping input, bu (my semantics [currently not implmented]).
        # Inhibitory: lateral (other Ps in child, and, if in DORA mode, other PO objects not connected to my RB, and 3*PO connected to my RB), inhibitor.
        # get my exhitatory input.
        # td.
        # td from my RBs, ONLY if in the second phase_set or above.
        # (NOTE: phase_set counts from 0, so phase_set == 1 is the second phase_set.)
        if phase_set >= 1:
            for myRB in self.myParentRBs:
                self.td_input += myRB.act
        # bu (input from semantics; not implemented yet).
        # mapping input.
        for mappingConnection in self.mappingConnections:
            self.map_input += ((3*mappingConnection.weight*mappingConnection.driverToken.act) - (self.max_map*mappingConnection.driverToken.act) - (mappingConnection.driverToken.max_map*mappingConnection.driverToken.act))
        # get inhibitory input.
        # lateral input.
        # from other P units in child mode.
        for myP in memory.recipient.Ps:
            if myP.mode == -1 and myP is not self:
                self.lateral_input == myP.act*lateral_input_level
        # if in DORA mode, from PO units not in the same RB as me, and from PO units in the same RB as me*3.
        for myPO in memory.recipient.POs:
            if asDORA:
                # make sure that the PO is not connected to the same RB as me.
                # for each RB I am connected to make sure that RB is not in PO's RBs.
                same_RB = False
                for myRB in self.myRBs:
                    if myRB in myPO.myRBs:
                        same_RB = True
                        break
                # if same_RB is false, get inhibition from the myPO.
                if not same_RB:
                    self.lateral_input -= myPO.act
            else: # if I'm in LISA mode.
                if myPO.predOrObj == 0: # i.e., if the PO is an object.
                    self.lateral_input -= myPO.act


class RBUnit(TokenUnit):
    def __init__(self, my_name, my_set, analog, inferred_now, myanalog):
        TokenUnit.__init__(self, my_name, my_set, analog, inferred_now, myanalog) # default init for all tokens.
        self.my_type = 'RB'
        self.myParentPs = [] # eventually connections to my P units: Initialized to None.
        self.myPred = [] # eventually connections to my pred unit: Initialized to None.
        self.myObj = [] # eventually connections to my object unit: Initialized to None.
        self.myChildP = [] # eventually connections to my child P unit: Initialized to None.
        self.myParentRB = []
        self.myChildRB = []
        self.timesFired = 0.0
        self.inhibitorThreshold = 160 ######### NOTE: THIS MIGHT NEED TO BE CHANGED LATER.
        self.mode = 0 # as default mode is neutral.
    
    def get_index(self, memory):
        self.my_index = memory.RBs.index(self)
    
    def initialize_timesFired(self):
        self.timesFired = 0.0
    
    def update_timesFired(self): # update my timesFired.
        self.timesFired += 1 # also add 1 to times fired.
    
    def update_inhibitor_act(self):
        if self.inhibitor_input >= self.inhibitorThreshold:
            self.inhibitor_act = 1
    
    def get_RBmode(self): # set my RB mode.
        # set RBmode to 1 (Parent) if input from my RBs below me is greater than input from RBs above me, set RBmode to -1 (child) if input from RBs above me is greater than input from RBs below me, and set RBmode to 0 (neutral) otherwise.
        # get the input from RBs below me and RBs above me.
        parent_input = 0
        child_input = 0
        for myRB in self.myChildRB:
            parent_input += myRB.act
        for myParentRB in self.myParentRB:
            child_input += myParentRB.act
        if parent_input > child_input:
            self.mode = 1
        elif self.act > 0.0 and len(self.myParentRB) > 0:
            self.mode = -1
        else:
            self.mode = 0
    
    def update_input_driver(self, memory, asDORA):
        # update RB inputs:
        # sources of input:
        # Exitatory: td (my P), bu (my POs).
        # Inhibitory: lateral (other RBs*3), inhibitor.
        # get my exitatory input.
        # get td from my P
        for myP in self.myParentPs:
            self.td_input += myP.act
        # get bu from my POs and child Ps (as long as you have objects and child Ps). (Notice you are using the 0th element because RBs have only one pred and one object/childP.)
        if len(self.myPred) >= 1:
            self.bu_input += self.myPred[0].act
        if len(self.myObj) >= 1:
            self.bu_input += self.myObj[0].act
        if len(self.myChildP) >= 1:
            self.bu_input += self.myChildP[0].act
        # get my inhibitor input.
        # get lateral inhibtion from other RBs that are not me.
        for myRB in memory.driver.RBs:
            if myRB is not self:
                self.lateral_input -= myRB.act*10
        # get lateral inhibition from my inhibitor.
        self.lateral_input -= self.inhibitor_act*10
    
    def update_input_recipient(self, memory, asDORA, phase_set, lateral_input_level):
        # update RB inputs:
        # Units in parent mode:
        # sources of input:
        # Exitatory: td (my P units), bu (my pred and obj POs, and my child Ps), mapping input.
        # Inhibitory: lateral (other RBs*3), inhbitor.
        # get my exhitatory input.
        # td.
        # td from my Ps, ONLY if in the second phase_set or above.
        # (NOTE: phase_set counts from 0, so phase_set == 1 is the second phase_set.)
        if phase_set >= 1:
            for myP in self.myParentPs:
                self.td_input += myP.act
        # get bu from my POs and child Ps (as long as you have objects and child Ps). (Notice you are using the 0th element because RBs have only one pred and one object/childP.)
        if len(self.myPred) >= 1:
            self.bu_input += self.myPred[0].act
        if len(self.myObj) >= 1:
            self.bu_input += self.myObj[0].act
        if len(self.myChildP) >= 1:
            self.bu_input += self.myChildP[0].act
        if len(self.myChildRB) >= 1:
            self.bu_input += self.myChildRB[0].act
        # mapping input.
        # mapping input is for each similar token unit in the driver, 3*(driver.act*mapping_weight) - max(mapping_weight_driver_unit) - max(own_mapping_weight).
        for mappingConnection in self.mappingConnections:
            self.map_input += ((3*mappingConnection.weight*mappingConnection.driverToken.act) - (self.max_map*mappingConnection.driverToken.act) - (mappingConnection.driverToken.max_map*mappingConnection.driverToken.act))
        # get inhibitory input.
        # lateral inhibition.
        # inhition from RBs that are NOT me.
        for myRB in memory.recipient.RBs:
            if (myRB is not self) and (myRB.mode != -1) and (myRB not in self.myParentRB):
                self.lateral_input -= myRB.act*lateral_input_level
        # inhibition from inhibitor.
        self.lateral_input -= self.inhibitor_act*10


class POUnit(TokenUnit):
    def __init__(self, my_name, my_set, analog, inferred_now, myanalog, am_pred):
        TokenUnit.__init__(self, my_name, my_set, analog, inferred_now, myanalog) # default init for all tokens.
        self.my_type = 'PO'
        self.predOrObj = am_pred # 1 for pred, 0 for object.
        self.myRBs = [] # connections to my RBs: Initialized to empty.
        self.same_RB_POs = [] # connections to POs connected to same RB as me.
        self.mySemantics = [] # connections to Links (datatype defined below) to semantics. (Links include info on who they connect to and connection weight.)
        self.semNormalization = None # here's where you'll store information on the number of semantics for semantic normalization.
        self.max_sem_weight = None # here's where you'll store information on my maximum semantic weight.
        self.inhibitorThreshold = 110 ######### NOTE: THIS MIGHT NEED TO BE CHANGED LATER.
    
    def get_index(self, memory):
        self.my_index = memory.POs.index(self)
    
    def update_inhibitor_act(self):
        if self.inhibitor_input >= self.inhibitorThreshold:
            self.inhibitor_act = 1
    
    def update_input_driver(self, memory, asDORA):
        # update PO inputs:
        # sources of input:
        # Exitatory: td (my RB) * gain (2 for preds, 1 for objects).
        # Inhibitory: lateral (other POs not connected to my RB and Ps in child mode, if in DORA mode, then other PO connected to my RB), inhibitor.
        # get my exitatory input.
        # td.
        for myRB in self.myRBs:
            if self.predOrObj == 1:
                self.td_input += myRB.act*2
            else:
                self.td_input += myRB.act
        # get my inhibitory input.
        # get lateral inhibition from POs not connected to my RB and are not me.
        for myPO in memory.driver.POs:
            connected_to_my_RB = False
            if myPO in self.same_RB_POs:
                connected_to_my_RB = True
            if connected_to_my_RB:
                if (myPO is not self) and asDORA:
                    self.lateral_input -= myPO.act*3
            else:
                if myPO is not self:
                    self.lateral_input -= myPO.act*3
        # get lateral inhibition from my inhibitor.
        self.lateral_input -= self.inhibitor_act*10
    
    def update_input_recipient(self, memory, asDORA, phase_set, lateral_input_level, ignore_object_semantics=False):
        # update PO inputs:
        # if you are inferred, just set input = 10, otherwise, update normally.
        # NOTE: Why did I bother with setting inferred POs to high input?
        if self.inferred:
            # NOTE: Right now this bit of code is a place holder for setting the net_input of newly inferred units. The thinking is that it is possible that being able to do so might be useful in the future, although I'm getting less and less certain that this ability will be important at all. Nevertheless, it's still here just in case. 
            #self.net_input = 10.0
            pass
        else: # update normally.
            # sources of input:
            # Exitatory: td (my RBs), bu (my semantics [remember to normalize by number of semantics I connect to]), mapping input.
            # Inhibitory: lateral (all POs not connected to same RB as me, all Ps in child mode, and, if asDORA, PO connected to same RB as me*3), td (inhibition from active RBs to which I am not connected), inhibitor.
            # get my exhitatory input.
            # td from my RBs, ONLY if in the second phase_set or above.
            # (NOTE: phase_set counts from 0, so phase_set == 1 is the second phase_set.)
            if phase_set >= 1:
                for myRB in self.myRBs:
                    if self.predOrObj == 1:
                        self.td_input += myRB.act*2
                    else:
                        self.td_input += myRB.act
            # bu input from my semantics. Remeber that you divisively normalize by the number of semantics the PO is connected to above threshold(=.1).
            semantic_input = 0
            # tally up all semantic input.
            for semanticLink in self.mySemantics:
                semantic_input += semanticLink.mySemantic.act * semanticLink.weight
            # now my bu_input is semantic_input divided by self.semanticNormalization.
            # insert a try/except for DEBUGGINGself.
            try:
                self.bu_input = semantic_input / self.semNormalization
            except:
                pdb.set_trace()
            # mapping input.
            # mapping input is for each similar token unit in the driver, 3*(driver.act*mapping_weight) - max(mapping_weight_driver_unit) - max(own_mapping_weight).
            for mappingConnection in self.mappingConnections:
                # get mapping input only from PO tokens that are in the same mode as I am (i.e., preds get input from preds, and objs get input from objs). 
                if mappingConnection.driverToken.predOrObj == self.predOrObj: 
                    self.map_input += (3*(mappingConnection.weight*mappingConnection.driverToken.act) - (self.max_map*mappingConnection.driverToken.act) - (mappingConnection.driverToken.max_map*mappingConnection.driverToken.act))
            # get inhibitory input.
            # lateral inhibition.
            # all POs not connected to same RB as me, and, if asDORA, POs in same RB as me, unless the PO is newly inferred, in which case it doesn't inhibit anything.
            for myPO in memory.recipient.POs:
                connected_to_my_RB = False
                if myPO in self.same_RB_POs:
                    connected_to_my_RB = True
                if connected_to_my_RB:
                    if (myPO is not self) and asDORA:
                        # if not myPO.inferred: I've removed this if-statement becauase I don't think it helps.
                        self.lateral_input -= myPO.act*(lateral_input_level*2) # the 2 here is a place-holder for a multiplier for within RB inhibition (right now it is a bit higher than between RB inhibition).
                else:
                    # by default, POs not connected to your RB inhibit you), however, if ignore_object_semantics==True, then PO preds only inhibit other PO preds, and PO objects only inhibit other PO objects.
                    if ignore_object_semantics==True:
                        if (myPO is not self) and (PO.predOrObj == self.predOrObj):
                    	    self.lateral_input -= myPO.act*lateral_input_level
                    else:
                        if (myPO is not self):
                            self.lateral_input -= myPO.act*lateral_input_level
            #pdb.set_trace()
            # all Ps in child mode.
            for myP in memory.recipient.Ps:
                if myP.mode == -1: # if P unit is in child mode.
                    # if I am in DORA mode, get inhibitory input if not in same RB as me.
                    if asDORA:
                        # make sure PO is not in my myRB.
                        sameRB = False
                        for myRB in self.myRBs:
                            if myRB in myP.myParentRBs:
                                sameRB = True
                                break
                        if not sameRB:
                            self.lateral_input -=P.act*3
                    else: # If I'm in LISA mode.
                        # get inhibitory input from that P if I am an object.
                        if self.predOrObj == 0:
                            self.lateral_input -= myP.act*lateral_input_level
            # td inhibitory input from RBs I am not connected to.
            # NOTE: td inhibition from unconnected RBs occurs ONLY in DORA mode and ONLY if in the second phase_set or above (NOTE: phase_set counts from 0, so phase_set == 1 is the second phase_set).
            if asDORA and phase_set >=1:
                for myRB in memory.recipient.RBs:
                    # if the RB is NOT in myRBs
                    if not (myRB in self.myRBs):
                        self.td_input -= myRB.act*1 # NOTE: you might want to set the multiplier on other RB inhibition to lateral_input_level.
            # my inhibitor.
            self.lateral_input -= self.inhibitor_act*10
            # for debugging.
    
    # NOTE THAT THIS FUNCTION MIGHT NEED SOME WORK!
    def get_weight_length(self): # how many semantics am I connected to with weight > .1? Used to normalize input so not affected by raw number of semantics.
        # find out how many semntics I'm connected to with weight greater than .1.
        # initialize my weight length and remove any connections less than 0.1.
        my_weight_length = 0
        for link in self.mySemantics:
            if link.weight > .1:
                my_weight_length += link.weight
        self.semNormalization = my_weight_length
    
    # function to semantics I am most strongly connected to.
    def get_max_semantic_weight(self):
        # find the my maximum semantic connection weight.
        self.max_sem_weight = 0.0
        for link in self.mySemantics:
            if link.weight > self.max_sem_weight:
                self.max_sem_weight = link.weight


class Semantic(object):
    def __init__(self, my_name, dimension=None, amount=None, ont_status='state'):
        self.name = my_name
        self.my_type = 'semantic'
        self.dimension = dimension # if I code a dimension, which dimension?; else = None.
        self.amount = amount # if I am a metric dimension, my value on that dimension; else = None.
        self.ont_status = ont_status # what is my ontological status? Am I a 'state' (i.e., an indication of the existence of a property) or a 'value' (i.e., a specific aboslute value on some dimension)? NOTE: comparative semantics like more/less/same/different have ont_status of 'SDM'.
        self.myinput = 0.0
        self.max_sem_input = 0.0 # the maximum input to any semantic unit in the network.
        self.act = 0.0
        self.myPOs = [] # initialize to empty. Later it will have Links to POs.
    
    def update_input(self, memory, ignore_object_semantics=False, ignore_memory_semantics=False):
        self.myinput = 0.0
        for Link in self.myPOs:
            # make sure that I'm not getting input from newSet POs, that I'm ignoring input from object POs if ignore_object_semantics == True, and that I'm not getting input from memory units during retrieval if ignore_memory_semantics == True.
            if Link.myPO.set != 'newSet':
                if ignore_memory_semantics:
                    if Link.myPO.set != 'memory':
                        if ignore_object_semantics == True:
                            if Link.myPO.predOrObj==1:
                                self.myinput += Link.myPO.act * Link.weight
                        else:
                            self.myinput += Link.myPO.act * Link.weight
                else:
                    if ignore_object_semantics == True:
                        if Link.myPO.predOrObj==1:
                            self.myinput += Link.myPO.act * Link.weight
                    else:
                        self.myinput += Link.myPO.act * Link.weight
    
    def set_max_input(self, max_input):
        self.max_sem_input = max_input
    
    def update_act(self):
        if self.max_sem_input > 0:
            self.act = self.myinput / self.max_sem_input
        else:
            self.act = 0.0
    
    def initializeSem(self):
        self.act = 0.0
        self.myinput = 0.0
    
    def initialize_input(self, refresh):
        self.myinput = refresh


class Link(object):
    def __init__(self, my_PO, my_P, my_sem, weight):
        self.myPO = my_PO
        self.myP = my_P
        self.mySemantic = my_sem
        self.weight = weight

class localInhibitor(object):
    def __init__(self):
        self.act = 0.0
    
    def checkDriverPOs(self, memory):
        for myPO in memory.driver.POs:
            if myPO.inhibitor_act == 1.0:
                # set inhibitorActivation to 1.0.
                self.act = 1.0
    
    def fire_local_inhibitor(self,memory):
        # clear driver and recipient PO and semantic activation.
        for myPO in memory.driver.POs:
            myPO.initialize_act()
        for myPO in memory.recipient.POs:
            myPO.initialize_act()
        for semantic in memory.semantics:
            semantic.initializeSem()
        # return the updated memory.
        return memory


class globalInhibitor(object):
    def __init__(self):
        self.act = 0.0
    
    def checkDriverRBs(self, memory):
        fire_inhibitor = False
        for myRB in memory.driver.RBs:
            if myRB.inhibitor_act == 1.0:
                # clear driver and recipient PO and semantic activation.
                self.act = 1.0
    
    def fire_global_inhibitor(self, memory):
        # set the activation and input of all driver and recipient Ps, RBs and POs, and all semantics to 0.
        for myP in memory.driver.Ps:
            myP.initialize_act()
        for myP in memory.recipient.Ps:
            myP.initialize_act()
        for myRB in memory.driver.RBs:
            myRB.initialize_act()
        for myRB in memory.recipient.RBs:
            myRB.initialize_act()
        for myPO in memory.driver.POs:
            myPO.initialize_act()
        for myPO in memory.recipient.POs:
            myPO.initialize_act()
        for semantic in memory.semantics:
            semantic.initializeSem()
        # return the updated memory
        return memory


# analog class.
class Analog(object):
    def __init__(self):
        self.myGroups = []
        self.myPs = []
        self.myRBs = []
        self.myPOs = []
        self.total_act = 0.0
        self.num_units = None
        self.normalised_retrieval_act = None
    
    # function to sum up the number of token units in the analog. Used for retrieval routine.
    def sum_num_units(self):
        self.num_units = 0
        for myP in self.myPs:
            self.num_units += 1
        for myRB in self.myRBs:
            self.num_units += 1
        for myPO in self.myPOs:
            self.num_units += 1


# class to house the driver units.
class driverSet(object):
    def __init__(self):
        self.Groups = []
        self.Ps = []
        self.RBs = []
        self.POs = []
        self.analogs = []


# class to house the recipient units.
class recipientSet(object):
    def __init__(self):
        self.Groups = []
        self.Ps = []
        self.RBs = []
        self.POs = []
        self.analogs = []

# class to house the emerging recipient (newSet) units
class newSet(object):
    def __init__(self):
        self.Groups = []
        self.Ps = []
        self.RBs = []
        self.POs = []
        self.analogs = []

# class to house all the tokens for a simulation.
class memorySet(object):
    def __init__(self):
        self.Groups = []
        self.Ps = []
        self.RBs = []
        self.POs = []
        self.semantics = []
        self.Links = []
        self.mappingConnections = []
        self.mappingHypotheses = []
        self.localInhibitor = localInhibitor()
        self.globalInhibitor = globalInhibitor()
        self.driver = driverSet()
        self.recipient = recipientSet()
        self.newSet = newSet()
        self.to_add_Groups = []
        self.to_add_Ps = []
        self.to_add_RBs = []
        self.to_add_POs = []
        self.analogs = []

