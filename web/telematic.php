 <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
	<meta charset="UTF-8"> 
	<title>telematic.zhdk.ch - List of UDP ports</title>
</head>
<body>
	<h1>telematic.zhdk.ch - List of UDP ports</h1>
	<table border="1" cellpadding="5">
		<tr align="left">
			<th>Port-No.:</th>
			<th>Typ:</th>
			<th>Reserviert für:</th>
			<th>Connections:</th>
		</tr>
		<tr style="background-color:#FFDDFF">
			<td>4460</td>
			<td>dynmic UDP proxy</td>
			<td>tpf-server</td>
			<td></td>
		</tr>
		<tr>
			<td>4464 - 4483</td>
			<td>UDP proxy</td>
			<td></td>
			<td></td>
		</tr>
		<tr style="background-color:#DDDDFF">
			<td>4484</td>
			<td>UDP mirror</td>
			<td></td>
			<td></td>
		</tr>
		<!-- range 5000 - 5020 -->
		<tr>
			<td>5000</td>
			<td>UDP proxy</td>
			<td></td>
			<td></td>
		</tr>
		<tr>
			<td>5002</td>
			<td>UDP proxy</td>
			<td></td>
			<td></td>
		</tr>
		<tr>
			<td>5004</td>
			<td>UDP proxy</td>
			<td></td>
			<td></td>
		</tr>
		<tr>
			<td>5006</td>
			<td>UDP proxy</td>
			<td></td>
			<td></td>
		</tr>
		<tr>
			<td>5008</td>
			<td>UDP proxy</td>
			<td></td>
			<td></td>
		</tr>
		<tr>
			<td>5010</td>
			<td>UDP proxy</td>
			<td>UltraGrid</td>
			<td></td>
		</tr>
		<tr>
			<td>5012</td>
			<td>UDP proxy</td>
			<td>UltraGrid</td>
			<td></td>
		</tr>
		<tr>
			<td>5014</td>
			<td>UDP proxy</td>
			<td>UltraGrid</td>
			<td></td>
		</tr>
		<tr>
			<td>5016</td>
			<td>UDP proxy</td>
			<td>UltraGrid</td>
			<td></td>
		</tr>
		<tr>
			<td>5018</td>
			<td>UDP proxy</td>
			<td>UltraGrid</td>
			<td></td>
		</tr>
		<tr>
			<td>5020</td>
			<td>UDP proxy</td>
			<td>UltraGrid</td>
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
			<dd>allows 1-to-N connections, where the sender connects to the given port and all receivers connect to given Port + 2.</dd>
		</ div>
	</dl> 
</body>
</html>

