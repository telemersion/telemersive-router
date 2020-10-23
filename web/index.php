 <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
	<meta charset="UTF-8"> 
	<title>telematic.zhdk.ch - List of UDP ports</title>
</head>
<body>
	<h1>telematic server ports: <a href="telematic.php">overview</a>)</h1>
	<h1>IA.[space] server ports: <a href="iaspace1.php">overview</a>)</h1>
	<h1>telematic.zhdk.ch - List of Example UDP ports</h1>
	<table border="1" cellpadding = "5">
		<tr align="left">
			<th>ports</th>
			<th>service</th>
			<th>use</th>
			<th>connection</th>
		</tr>
		<tr style="background-color:#AADDDD">
			<td>10100</td>
			<td>UDP proxy</td>
			<td>for Audio</td>
			<td></td>
		</tr>
		<tr style="background-color:#AADDDD">
			<td>10101</td>
			<td>UDP proxy</td>
			<td>for Audio</td>
			<td></td>
		</tr>
		<tr style="background-color:#BBDDDD">
			<td>10200</td>
			<td>UDP multi proxy</td>
			<td>for OSC</td>
			<td></td>
		</tr>
		<tr style="background-color:#BBDDDD">
			<td>10201</td>
			<td>UDP multi proxy</td>
			<td>for OSC</td>
			<td></td>
		</tr>
		<tr style="background-color:#CCDDDD">
			<td>10250</td>
			<td>UDP multi proxy</td>
			<td>for MoCap</td>
			<td></td>
		</tr>
		<tr style="background-color:#CCDDDD">
			<td>10251</td>
			<td>UDP multi proxy</td>
			<td>for MoCap</td>
			<td></td>
		</tr>
		<tr style="background-color:#FFDDDD">
			<td>10300</td>
			<td>UDP proxy</td>
			<td>for UltraGrid</td>
			<td></td>
		</tr>
		<tr style="background-color:#FFDDDD">
			<td>10500</td>
			<td>UDP multi proxy</td>
			<td>for UltraGrid</td>
			<td></td>
		</tr>
		<tr style="background-color:#FFDDDD">
			<td>10501</td>
			<td>UDP multi proxy</td>
			<td>for UltraGrid</td>
			<td></td>
		</tr>
		<tr style="background-color:#FFDDDD">
			<td>10502</td>
			<td>UDP multi proxy</td>
			<td>for UltraGrid</td>
			<td></td>
		</tr>
	</table>
	<dl>
		<dt><b>UDP proxy</b></dt>
		<dd>connects two endpoints and relays datagrams between them</dd>
		<div style="background-color:#DDDDFF">
			<dt><b>UDP mirror</b></dt>
			<dd>sends incoming datagram back to source IP:port</dd>
		</div>
		<div style="background-color:#FFDDFF">
			<dt><b>dynamic UDP proxy</b><dt>
			<dd>manages multiple pairs of endpoints and relays datagrams between two linked endpoints (please refer to: <a href="https://gitlab.zhdk.ch/TPF/tpf-server">tpf-server</a>)</dd>
		</ div>
		<div style="background-color:#FFDDDD">
			<dt><b>UDP multi proxy</b><dt>
			<dd>allows 1-to-N connections, where the sender connects to the given port and all receivers connect to given Port + 5.</dd>
		</ div>
	</dl> 
</body>
</html>

