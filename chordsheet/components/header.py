def header():
	writeText(ls.title.cdata, size=24)
	writeText("Composer: {c}".format(c = ls.composer.cdata), size=12)
	writeText("Arranger: {a}".format(a = ls.arranger.cdata), size=12)