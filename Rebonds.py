from tkinter import *
import numpy as np
from scipy.optimize import curve_fit
from math import floor, sqrt
import itertools

hauteur, largeur=500, 500
nombre_clic_droit=0 #pour définir le segment de départ
coos_courbe=[] #pour stocker les coos d'une courbe en construction
elements=[] #toutes les courbes et segments obstacles
ready=False #pour le test de tangente

class segment:
    def __init__(self,x1,y1,x2,y2,couleur="black"):
        self.x1=x1
        self.y1=y1
        self.x2=x2
        self.y2=y2
        #ax+by+c=0
        if x1==x2:
            self.a=1
            self.b=0
            #self.c=-x1
        elif y1==y2:
            self.a=0
            self.b=1
            #self.c=-y1
        else:
            self.a=-(y2-y1)/(x2-x1)
            self.b=1
            #self.c=-(y1+self.a*x1)
        
        self.decalage_x=x2-x1
        self.decalage_y=y2-y1

        self.longueur=np.linalg.norm(np.array((x2,y2))-np.array((x1,y1)))
        self.avance_x=self.decalage_x/self.longueur
        self.avance_y=self.decalage_y/self.longueur

        trait=milieu2D([(round(x1),round(y1)),(round(x2),round(y2))],[])
        #on rajoute la même ligne décalée de 1, pour avoir une épaisseur de ligne qui ne permette pas de passer au travers
        self.pixels=[]
        for i in trait:
            self.pixels.append(i)
            self.pixels.append((i[0]+1,i[1]))
        self.ligne=Canevas.create_line(0,0,1,1,fill=couleur,width=2)

    def maj_decalage(self,decal_x,decal_y):
        self.decalage_x=decal_x
        self.decalage_y=decal_y
        self.avance_x=self.decalage_x/self.longueur
        self.avance_y=self.decalage_y/self.longueur
    def affichage(self):
        Canevas.coords(self.ligne,self.x1,self.y1,self.x2,self.y2)

def flatten(list_of_lists):
    #étale la liste de tuple : [(a,b),(c,d)] --> a,b,c,d
    return itertools.chain.from_iterable(list_of_lists)

def func_approx3(x,a,b,c,d):
    return [a*i**3+b*i**2+c*i+d for i in x]

def func_approx2(x,a,b,c):
    return [a*i**2+b*i+c for i in x]

class courbe:
    def __init__ (self, coos):
        self.coos=coos
        self.pixels=[]
        for i in range(len(coos)-1):
            self.pixels+=milieu2D([(round(coos[i][0]),round(coos[i][1])),(round(coos[i+1][0]),round(coos[i+1][1]))],[])
        self.approximation=Canevas.create_line([(0,0),(1,1)],fill="red",width=3,smooth=1)
        self.ligne=Canevas.create_line(0,0,1,1,smooth=1,fill="black",width=2)
    def derivation(self,indice):
        #approximation de la fonction autour du point considéré
        etendue=10
        x,y=[],[]
        for i in range(indice-etendue,indice+etendue):
            if i>=0 and i<len(self.pixels):
                x.append(self.pixels[i][0])
                y.append(self.pixels[i][1])
        param, param_cov = curve_fit(func_approx2, x, y)
        y_approx=func_approx2(x,param[0],param[1],param[2])
        self.new_coos=[(x[i],y_approx[i]) for i in range(len(x))]
        #derivation au point voulu
        h=0.1
        x=self.pixels[indice][0]
        self.derivee=(func_approx2([x+h],param[0],param[1],param[2])[0] - func_approx2([x],param[0],param[1],param[2])[0]) / h

    def affichage(self):
        Canevas.coords(self.ligne,*flatten(self.coos))
        
def demo_tangente(pourcentage):
    global trace, tangente, ready, elements
    if not ready:
        trace=elements[-1]
        tangente=segment(0,0,1,1,couleur="blue")
        tangente.affichage
        ready=True
    '''
    y=f'(a)(x-a)+f(a)
    y=ax+b
    avec a=f'(a)
    et b=-f'(a)*a+f(a)
    '''
    #calcul l'indice de la liste auquel on trouve le (x,y) où calculer la tangente
    indice=int(round(float(pourcentage)/100*(len(trace.pixels)-1)))
    #obtenir la dérivée
    trace.derivation(indice)
    #y=ax+b
    a=trace.derivee
    b=-a*trace.pixels[indice][0]+trace.pixels[indice][1]
    #segment à tracer pour visualiser la tangente
    x1=trace.pixels[indice][0]-20
    y1=a*x1+b
    x2=trace.pixels[indice][0]+20
    y2=a*x2+b
    Canevas.coords(tangente.ligne,x1,y1,x2,y2)
    Canevas.coords(trace.approximation,*flatten(trace.new_coos))


class lumiere:
    #comprend tous les segments de lumière lorsqu'il y a des réflexions
    def __init__(self,bouts):
        self.bouts=bouts
    def ajout_bout(self,xp,yp,decal_x,decal_y):
        x1=self.bouts[-1].x1
        y1=self.bouts[-1].y1
        Canevas.delete(self.bouts[-1].ligne)
        self.bouts.pop()
        self.bouts.append(segment(x1,y1,xp,yp,"red"))
        self.bouts.append(segment(xp,yp,xp+decal_x/self.bouts[-1].longueur,yp+decal_y/self.bouts[-1].longueur,"red"))
    def maj_coos(self):
        #le dernier met à jour ses coordonnées arrière en avançant
        self.bouts[0].x1+=self.bouts[0].avance_x
        self.bouts[0].y1+=self.bouts[0].avance_y
        if round(self.bouts[0].x1)==round(self.bouts[0].x2):
            Canevas.delete(self.bouts[0].ligne)
            self.bouts.remove(self.bouts[0])
        #le premier met à jour ses coordonnées avant en avançant
        self.bouts[-1].x2+=self.bouts[-1].avance_x
        self.bouts[-1].y2+=self.bouts[-1].avance_y
    def affichage(self):
        for segment in self.bouts:
            Canevas.coords(segment.ligne,segment.x1,segment.y1,segment.x2,segment.y2)

def Clic_gauche(event):
    global x_clic, y_clic
    x_clic=event.x
    y_clic=event.y
    #Canevas.create_rectangle(event.x, event.y, event.x+2, event.y+2,outline="white", fill="black")

def Clic_droit_survol(event):
    global x_clic, y_clic,coos_courbe
    coos_courbe.append((event.x,event.y))

def Clic_gauche_release(event):
    global elements
    if event.x != x_clic or event.y != y_clic:
        ligne=segment(x_clic,y_clic,event.x,event.y)
        ligne.affichage()
        elements.append(ligne)

def Clic_droit_release(event):
    global coos_courbe, elements, ready
    if len(coos_courbe)>1:
        trace=courbe(coos_courbe)
        trace.affichage()
        coos_courbe=[]
        elements.append(trace)
        ready=False
        pourcentage.set(0)

def Clic_droit(event):
    global nombre_clic_droit,x_depart, y_depart,x_arrivee, y_arrivee, laser
    if nombre_clic_droit==0:
        Canevas.create_rectangle(event.x, event.y, event.x+2, event.y+2,outline="white", fill="red")
        nombre_clic_droit+=1
        x_depart, y_depart=event.x, event.y
    elif nombre_clic_droit==1:
        nombre_clic_droit+=1
        x_arrivee, y_arrivee=event.x, event.y
        trait=segment(x_depart,y_depart,x_arrivee,y_arrivee,couleur="red")
        trait.affichage()
        laser=lumiere([trait])

def signe(n):
    if n==0:
        return 1
    return abs(n)/n

def distance2D(a,b):
	a=np.array(a)
	b=np.array(b)
	l=np.linalg.norm(b-a)
	return l

def milieu2D(file,complet):
    #obtient tous les points situés entre deux points sur une grille par le chemin le plus court (ligne droite, pas calcul de distance), fonction récursive
	if len(file)==1:
		return complet
	nouveau=(floor((file[-1][0]+file[-2][0])/2),floor((file[-1][1]+file[-2][1])/2))
	if distance2D(nouveau,file[-1])<=sqrt(2):
		complet.append(file[-1])
		if nouveau!=file[-1]:
			file.pop()
			file.append(nouveau)
		else:
			file.pop()
	else:
		file=file[:-1]+[nouveau]+file[-1:]
	milieu2D(file,complet)
	return complet

def mouvement():
    global laser, elements, ready, nombre_clic_droit, tangente
    rebond=Canevas.create_line(0,0,1,1,fill="blue")
    #on récupère les coordonnées
    premier=laser.bouts[-1]
    actu_x=premier.x2
    actu_y=premier.y2
    #on regarde la prochaine position théorique
    next_x=actu_x+premier.avance_x
    next_y=actu_y+premier.avance_y
    #on obtient tous les pixels se trouvant entre la position actuelle et la prochaine position
    tous_pixels=milieu2D([(round(actu_x),round(actu_y)),(round(next_x),round(next_y))],[])
    #si un de ces pixels appartient à un obstacle, on calcule la nouvelle trajectoire
    for pixel in tous_pixels:
        stop=False
        for element in elements:
            stop=False
            #si un des pixels de la trajectoire prévue fait partie d'un segment obstacle, alors il y a collision
            if pixel in element.pixels:
                if isinstance(element,segment):
                    paroi=element
                else:
                    indice=element.pixels.index(pixel)
                    #obtenir la dérivée
                    element.derivation(indice)
                    #y=ax+b
                    a=element.derivee
                    b=-a*element.pixels[indice][0]+element.pixels[indice][1]
                    #segment à tracer pour visualiser la tangente
                    x1=element.pixels[indice][0]-10
                    y1=a*x1+b
                    x2=element.pixels[indice][0]+10
                    y2=a*x2+b
                    Canevas.coords(rebond,x1,y1,x2,y2)
                    paroi=segment(x1,y1,x2,y2,couleur="green")
                #(u1,u2) vecteur normal à la droite sur laquelle rebondit le laser (segment ou tangente)
                u1=paroi.a
                u2=paroi.b
                #ax+by+c=0 l'équation de la droite de vecteur directeur (u1,u2)
                a=u2
                b=-u1
                c=-u2*pixel[0]+u1*pixel[1]
                #calcul du nouveau décalage d'avancement du laser d'après la réflexion
                if b==0:
                    decal_x=-premier.decalage_x
                    decal_y=premier.decalage_y
                elif a==0:
                    decal_x=premier.decalage_x
                    decal_y=-premier.decalage_y
                else:
                    #ici pour trouver le décalage je fais la symétrie de la fin du laser par rapport à la droite ax+by+c située plus haut
                    x1=premier.x1
                    y1=premier.y1
                    y2=((a/2)*(2*x1+y1*u2/u1)+y1*b/2+c)*2/(a*u2/u1-b)
                    x2=(y1-y2)*u2/u1+x1
                    decal_x=x2-pixel[0]
                    decal_y=y2-pixel[1]

                #après une réflexion la fin du laser n'a pas encore rebondi
                laser.ajout_bout(pixel[0],pixel[1],decal_x,decal_y)
                stop=True
                break
        if stop:
            break
    #on met à jour les coordonnées du laser
    laser.maj_coos()
    #on affiche la laser à la nouvelle position
    laser.affichage()

    recursif = fenetre.after(20,mouvement)
    if actu_x<0 or actu_x>largeur or actu_y<0 or actu_y>hauteur:
        fenetre.after_cancel(recursif)
        Canevas.delete(ALL)
        pourcentage.set(0)
        ready=False
        nombre_clic_droit=0



fenetre=Tk()

Canevas=Canvas(fenetre, height=hauteur, width=largeur)
Canevas.pack(side=LEFT)

Canevas.bind('<Button-1>',  Clic_gauche)
Canevas.bind('<B3-Motion>',  Clic_droit_survol)
Canevas.bind('<ButtonRelease-1>',  Clic_gauche_release)
Canevas.bind('<ButtonRelease-3>',  Clic_droit_release)
Canevas.bind('<Button-3>',  Clic_droit)

lancer = Button(fenetre,  text = 'Lancer',  command = mouvement)
lancer.pack()
pourcentage=StringVar()
pourcentage.set(0)
echelle=Scale(fenetre,  orient='horizontal',  from_=0,  to=100,  resolution=1,  tickinterval=20,  label='Démo tangente',  variable=pourcentage,  command=demo_tangente)
echelle.pack()
Bouton1 = Button(fenetre,  text = 'Quitter',  command = fenetre.destroy)
Bouton1.pack()


fenetre.mainloop()