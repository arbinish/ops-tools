#!/usr/bin/env python

import pygtk, gtk, gobject, pango, thread, os
pygtk.require('2.0')

gobject.threads_init()

class Timer():
	def __init__(self):
		self.x = 0
		self.pw = ''
		self.g = 0
		self.maxlen = 7
		self.symbols = 'abcd&#*)_=+9876543!@~|}{'
		self.Win()
		
	def start_t(self, widget):
#		self.g = gobject.timeout_add(100, self.count)
		self.symbols = ''.join(list(set(self.symbols)))
		thread.start_new_thread(self.permute, ('', 1))
		
	def Win(self):
		self.win = gtk.Window()
		self.win.set_size_request(600,50)
		self.win.set_position(gtk.WIN_POS_CENTER)
		self.win.connect('destroy', lambda Q: gtk.main_quit())
		self.win.show()
		
#		self.box1 = gtk.HBox()
#		self.win.add(self.box1)
#		self.box1.show()
		
		self.label = gtk.Label(str(self.x))
		self.label.modify_font(pango.FontDescription('sans 28'))
#		self.box1.pack_start(self.label)
#		self.label.show()
		
		self.button = gtk.Button('Start')
		self.button.set_size_request(100,40)
#		self.box1.pack_start(self.button, 1)
		self.button.connect('clicked', self.start_t)
#		self.button.show()
		
		fixed = gtk.Fixed()
		fixed.put(self.label, 105,5)
		fixed.put(self.button, 500,5)
		
		self.win.add(fixed)
		self.win.show_all()
		
	def permute(self, buf, pos):
		if (len(buf) >= self.maxlen):
			self.label.set_text(buf)
			self.pw = buf
			if (buf == '!@!!abc'):
				print "Gotcha"
				os.sys.exit(0)
			return
		for c in self.symbols:
			self.permute(buf+c, pos+1)

	def count(self):
#		self.x += 1
		#self.label.set_text(str(self.x))
		self.label.set_text(self.pw)
		if (self.pw == '!!_abcd'): 
			print "Gotcha"
			return False
		return True
	
	
def main():
	gtk.main()
	

if __name__ == '__main__':
	window = Timer()
	main()
	
		
	
