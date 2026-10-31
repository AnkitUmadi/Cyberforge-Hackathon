# Dataset Profile: Fortinet FortiGate Log Telemetry

## Overview
- **Source File:** `data/sample_100MB.log` (extracted from `firex-10G.log`)
- **Total Lines Analyzed:** 198,613
- **Time Range:** `2026-10-23 08:48:26` to `2026-10-23 16:37:55`
- **Log Format:** Key-Value Pair format (`key=value` or `key="value"`) typical of Fortinet FortiOS / FortiGate UTM appliances.

## Event Hierarchy & Distribution
### High-level Types:
- **`traffic`**: 127,162 (64.0%)
- **`event`**: 41,396 (20.8%) 
- **`utm`**: 30,055 (15.1%)

### Subtypes Breakdown:
- **`traffic.forward`**: 127,162
- **`event.system`**: 31,277
- **`utm.webfilter`**: 8,939
- **`utm.ips`**: 6,092
- **`utm.dns`**: 6,059
- **`utm.app-ctrl`**: 5,988
- **`utm.virus`**: 2,977
- **`event.vpn`**: 2,900
- **`event.ha`**: 1,833
- **`event.dhcp`**: 1,819
- **`event.connector`**: 1,790
- **`event.sdwan`**: 1,777

### Severity Levels:
- **`notice`**: 142,014
- **`alert`**: 33,780
- **`information`**: 19,244
- **`warning`**: 2,978
- **`error`**: 597

## Security-Relevant Fields
### Top `logdesc` (Event Descriptions):
- `Admin login failed`: 27,688
- `HA device status`: 1,833
- `DHCP Ack log`: 1,819
- `Performance statistics`: 1,815
- `SD-WAN health-check status`: 1,777
- `DHCP statistics`: 1,773
- `Attribute configured`: 1

### Actions:
- `accept`: 118,151
- `login`: 27,688
- `pass`: 12,047
- `deny`: 9,011
- `passthrough`: 8,029
- `N/A`: 7,202
- `dropped`: 4,935
- `blocked`: 3,887
- `perf-stats`: 1,815
- `connect`: 1,790

### Statuses:
- `failed`: 27,688

### Top Usernames Observed:
- `admin`: 11,980
- `administrator`: 255
- `root`: 212
- `administrador`: 157
- `usuario`: 100
- `remote1`: 82
- `user`: 80
- `test`: 73
- `manager`: 69
- `remote_admin`: 53
- `remote`: 52
- `reception`: 49
- `warehouse`: 49
- `andres`: 47
- `acc4`: 47
- `remote2`: 46
- `remoteuser`: 44
- `scanner`: 43
- `pgsa`: 43
- `info`: 43

### Top Services / Protocols:
- `HTTPS`: 29,026
- `DNS`: 14,060
- `HTTP`: 11,009
- `SNMP`: 8,039
- `RTP`: 8,027
- `SSH`: 8,004
- `SIP`: 8,001
- `SMB`: 7,983
- `RDP`: 7,969
- `LDAP`: 7,938
- `SMTP`: 7,926
- `NTP`: 7,917
- `IMAPS`: 7,893
- `ICMP_ANY`: 7,864
- `Kerberos`: 7,790

### Top Applications:
- `TikTok`: 1,654
- `GitLab`: 1,654
- `BlackberryMessenger`: 1,648
- `HTTPS`: 1,643
- `Putty`: 1,638
- `Facebook`: 1,634
- `SCP`: 1,632
- `Zoom`: 1,632
- `Chocolatey`: 1,625
- `Jira`: 1,621
- `MicrosoftTeams`: 1,619
- `Twitter`: 1,617
- `Discord`: 1,612
- `WinX`: 1,606
- `Rydark`: 1,604

## All Discovered Field Keys (49 total)
`date` (198,613), `time` (198,613), `eventtime` (198,613), `tz` (198,613), `devname` (198,613), `devid` (198,613), `logid` (198,613), `type` (198,613), `subtype` (198,613), `level` (198,613), `vd` (198,613), `action` (198,613), `srcip` (187,806), `srcintfrole` (187,806), `dstip` (187,806), `dstintfrole` (187,806), `proto` (187,806), `srccountry` (187,806), `dstcountry` (187,806), `srcintf` (184,906), `dstintf` (184,905), `srcport` (157,217), `dstport` (157,217), `sessionid` (157,217), `service` (157,217), `policyid` (157,157), `sentbyte` (127,222), `rcvdbyte` (127,222), `sentpkt` (127,222), `rcvdpkt` (127,222), `duration` (127,162), `app` (75,991), `appcat` (75,991), `apprisk` (75,991), `msg` (41,396), `logdesc` (36,706), `user` (28,267), `ui` (27,689), `method` (27,689), `status` (27,688), `reason` (27,688), `hostname` (18,035), `url` (11,976), `catdesc` (8,939), `attack` (6,092), `attackid` (6,092), `severity` (6,092), `virus` (2,977), `crscore` (60)

## Representative Log Lines by Type

### Type: `utm`
```log
date=2026-10-23 time=08:48:26 eventtime=1792745306000000000 tz="+0530" devname="FGT60FTK00000000" devid="FGT60FTK00000000" logid="1501054600" type="utm" subtype="dns" level="information" vd="root" srcip=10.10.40.156 srcport=37918 srcintf="internal4" srcintfrole="lan" dstip=11.113.232.73 dstport=53 dstintf="wan1" dstintfrole="wan" sessionid=235524450 proto=17 action="pass" policyid=20 service="DNS" srccountry="Reserved" dstcountry="Ireland" hostname="nytimes.com"
```

### Type: `traffic`
```log
date=2026-10-23 time=08:48:26 eventtime=1792745306423348000 tz="+0530" devname="FGT60FTK00000000" devid="FGT60FTK00000000" logid="0000000013" type="traffic" subtype="forward" level="notice" vd="root" srcip=10.10.40.225 srcport=50951 srcintf="internal4" srcintfrole="lan" dstip=71.38.6.121 dstport=443 dstintf="wan1" dstintfrole="wan" sessionid=1309353623 proto=6 action="accept" policyid=4 service="RDP" srccountry="Reserved" dstcountry="Brazil" app="Discord" appcat="Email" apprisk="elevated" duration=274 sentbyte=17865 rcvdbyte=35730 sentpkt=14 rcvdpkt=26
```

### Type: `event`
```log
date=2026-10-23 time=08:48:26 eventtime=1792745306564464000 tz="+0530" devname="FGT60FTK00000000" devid="FGT60FTK00000000" logid="0100032002" type="event" subtype="system" level="alert" vd="root" logdesc="Admin login failed" user="admin" ui="https(209.50.167.232)" method="https" srcip=209.50.167.232 srcintf="wan1" srcintfrole="wan" dstip=10.10.99.1 dstintf="mgmt" dstintfrole="lan" proto=6 action="login" srccountry="India" dstcountry="Reserved" status="failed" reason="name_invalid" msg="Administrator admin login failed from https(209.50.167.232) because of invalid user name"
```
