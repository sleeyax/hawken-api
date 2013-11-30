# -*- coding: utf-8 -*-

from sleekxmpp import Message
from sleekxmpp.exceptions import IqError, IqTimeout
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.plugins.xep_0004 import Form
from sleekxmpp.xmlstream import register_stanza_plugin, ET
from hawkenapi.sleekxmpp.stanza import StormId, PartyMemberData, PartyVoiceChannel
from hawkenapi.util import enum


CancelCode = enum(PARTYCANCEL="0", LEADERCANCEL="1", LEADERCHANGE="2", NOMATCH="3", MEMBERJOIN="4", MEMBERLEFT="5", MEMBERKICK="6")


class Hawken_Party(base_plugin):
    """
    Hawken Party Plugin
    """
    name = "hawken_party"
    description = "Hawken: Party Support"
    dependencies = set(["xep_0045"])

    def plugin_init(self):
        # Register Stanzas
        register_stanza_plugin(Message, StormId)
        register_stanza_plugin(Message, PartyMemberData)
        register_stanza_plugin(Message, PartyVoiceChannel)

    def create(self, room, scallsign):
        # Join the room
        self.xmpp.plugin["xep_0045"].joinMUC(room, scallsign, wait=True)

        # Create the room config
        form = Form()
        form.set_type("submit")
        form.add_field(var="muc#roomconfig_publicroom", ftype="boolean", value="0")
        form.add_field(var="muc#roomconfig_allowinvites", ftype="boolean", value="1")
        form.add_field(var="muc#roomconfig_gametype", ftype="text-single", value="Game")

        # Configure the room
        self.xmpp.plugin["xep_0045"].configureRoom(room, form=form)

    def join(self, room, scallsign):
        # Join the room
        self.xmpp.plugin["xep_0045"].joinMUC(room, scallsign)

    def leave(self, room, scallsign):
        # Leave the room
        self.xmpp.plugin["xep_0045"].leaveMUC(room, scallsign)

    def invite(self, room, sender, sguid, scallsign, target, tcallsign, reason=""):
        # Send the invite to the player
        self.xmpp.plugin["xep_0045"].invite(room, target, reason=reason, mfrom=sender)

        # Build the message
        message = self.xmpp.make_message(room, mtype="groupchat", mfrom=sender)
        memberdata = message["partymemberdata"]
        memberdata["infoName"] = "InvitePlayerToParty"
        memberdata["playerId"] = sguid
        memberdata["infoValue"] = "{0} has invited {1} to the party.".format(scallsign, tcallsign)

        # Send invite notification
        message.send()

    def message(self, room, sender, sguid, body):
        # Build the message
        message = self.xmpp.make_message(mto=room, mtype="groupchat", mfrom=sender)
        message["body"] = body
        message["stormid"].id = sguid

        # Send party message
        message.send()

    def kick(self, room, tcallsign):
        # Do it by hand
        query = ET.Element("{http://jabber.org/protocol/muc#admin}query")
        item = ET.Element("{http://jabber.org/protocol/muc#admin}item", {"role": "none", "nick": tcallsign})
        query.append(item)
        iq = self.xmpp.makeIqSet(query)
        iq["to"] = room

        try:
            iq.send()
        except IqError:
            return False
        except IqTimeout:
            return False
        return True

    def leader_set(self, room, tcallsign):
        # Set the target as the owner
        self.xmpp.plugin["xep_0045"].setAffiliation(room, nick=tcallsign, affiliation="owner")

    def matchmaking_start(self, room, sender, sguid):
        # Build the message
        message = self.xmpp.make_message(room, mtype="groupchat", mfrom=sender)
        memberdata = message["partymemberdata"]
        memberdata["infoName"] = "PartyMatchmakingStart"
        memberdata["playerId"] = sguid
        memberdata["infoValue"] = "NoData"

        # Send matchmaking start notice
        message.send()

    def matchmaking_cancel(self, room, sender, sguid, code=CancelCode.PARTYCANCEL):
        # Build the message
        message = self.xmpp.make_message(room, mtype="groupchat", mfrom=sender)
        memberdata = message["partymemberdata"]
        memberdata["infoName"] = "PartyMatchmakingCancel"
        memberdata["playerId"] = sguid
        memberdata["infoValue"] = code

        # Send matchmaking cancel notice
        message.send()

    def deploy_start(self, room, sender, sguid, server):
        # Build the message
        message = self.xmpp.make_message(room, mtype="groupchat", mfrom=sender)
        memberdata = message["partymemberdata"]
        memberdata["infoName"] = "DeployPartyData"
        memberdata["playerId"] = sguid
        memberdata["infoValue"] = server

        # Send deploy start notice
        message.send()

    def deploy_cancel(self, room, sender, sguid, code=CancelCode.PARTYCANCEL):
        # Build the message
        message = self.xmpp.make_message(room, mtype="groupchat", mfrom=sender)
        memberdata = message["partymemberdata"]
        memberdata["infoName"] = "DeployCancelData"
        memberdata["playerId"] = sguid
        memberdata["infoValue"] = code

        # Send deploy cancel notice
        message.send()

    def game_start(self, room):
        # Create room config for update
        form = Form()
        form.set_type("submit")
        form.add_field(var="muc#roomconfig_gametype", ftype="text-single", value="Hawken")

        # Reconfigure the room
        self.xmpp.plugin["xep_0045"].configureRoom(room, form=form)

    def game_end(self, room):
        # Create room config for update
        form = Form()
        form.set_type("submit")
        form.add_field(var="muc#roomconfig_gametype", ftype="text-single", value="Game")

        # Reconfigure the room
        self.xmpp.plugin["xep_0045"].configureRoom(room, form=form)
