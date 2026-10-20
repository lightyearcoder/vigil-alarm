# Une tablette au mur comme clavier d'alarme

Ceci est une traduction de [tablet.md](tablet.md), traduite par Claude (une IA) et non relue par un locuteur natif. Merci de signaler les erreurs sous forme d'issue.

Vous pouvez utiliser Vigil avec une tablette qui affiche un tableau de bord Home Assistant, à la place du clavier ESPHome (ou à côté). La tablette est un clavier dans le registre, lié à un utilisateur Home Assistant, et elle affiche la **carte Vigil** : l'état, les boutons des modes qu'elle peut utiliser, un pavé numérique et, après le code installateur du clavier, les capteurs.

## La mettre en place

1. **Créez un utilisateur pour la tablette.** Dans Home Assistant : *Paramètres → Personnes → Utilisateurs → Ajouter un utilisateur*. Utilisez un utilisateur ordinaire. Vous pouvez choisir un compte administrateur à la place (il apparaît comme *(admin)* dans la liste), mais c'est votre responsabilité : les réglages du clavier s'appliquent alors à tout ce que ce compte fait, sur chaque appareil où il est connecté, et un appareil volé ou laissé sans surveillance est connecté en administrateur. Vigil ne donne à un tel compte aucun droit d'administrateur sur le clavier (un code est toujours nécessaire pour désactiver et neutraliser), et la meilleure solution est un second compte ordinaire pour l'usage quotidien.
2. **Enregistrez la tablette dans Vigil.** Ouvrez *Vigil Alarm → Claviers → Ajouter un clavier*. Donnez-lui un nom, choisissez *Tablette ou téléphone avec Home Assistant* comme type d'appareil et choisissez le compte sous *Compte Home Assistant (tablette ou téléphone)*. Réglez ce que la tablette peut faire (modes, désactivation, neutralisation, coupure du son, liste des capteurs, langue), exactement comme pour un clavier ESPHome. Définissez un **code installateur** pour le clavier si la tablette doit pouvoir afficher les capteurs.
3. **Connectez la tablette avec cet utilisateur** et ouvrez un tableau de bord avec la carte Vigil. Dans l'éditeur de tableau de bord, choisissez *Ajouter une carte → Personnalisée : Vigil*, ou en YAML :

   ```yaml
   type: custom:vigil-card
   ```

   Vigil charge la carte lui-même ; il n'y a rien à installer ni à ajouter comme ressource. La carte n'a aucun réglage hormis `idle_timeout` (secondes sans toucher avant qu'elle oublie un code à moitié saisi, 30 par défaut). Pour une tablette murale, utilisez une vue panneau (une seule carte) ou un tableau de bord de type kiosque, comme celui que Fully Kiosk Browser peut afficher, pour que la barre latérale soit masquée.
4. Utilisez **HTTPS** pour Home Assistant. Avec un simple `http://`, le code circule en clair sur votre Wi-Fi.

## Ce que fait la carte

![La carte sur un téléphone : pas prête, pavé numérique, activation avec compte à rebours, alarme](images/card-phone-states-en.png)

![La carte sur une tablette : deux colonnes, anneau et compte à rebours à gauche, boutons et pavé numérique à droite](images/card-tablet-states-en.png)

Avec un clavier (une tablette qui en a un, ou un ordinateur), vous pouvez saisir le code : chiffres, Retour arrière pour effacer, Entrée pour valider, Échap pour fermer le pavé numérique.

La carte affiche l'état sous forme d'anneau avec une icône, de la couleur de l'état ; pendant les temporisations de sortie et d'entrée, l'anneau est le compte à rebours. Elle suit la largeur dans laquelle elle se trouve : une colonne sur un téléphone, deux colonnes sur une tablette. Elle a le même aspect que le clavier tactile.

- Suit le profil du clavier de la tablette : seulement les modes dans lesquels ce clavier peut activer, *Désactiver* seulement s'il le peut, les boutons de neutralisation seulement s'il peut neutraliser, la langue choisie pour le clavier, et aucune liste de capteurs quand elle est sur *jamais*.
- **Désactiver et neutraliser demandent toujours un code utilisateur** ; activer n'en demande un que si *un code est nécessaire pour activer* est activé. Le pavé numérique ne s'ouvre jamais de lui-même : pendant la temporisation d'entrée et une alarme, l'écran montre d'abord ce qui se passe, et celui qui veut désactiver appuie sur *Désactiver*.
- **La liste des capteurs** s'ouvre avec le code de n'importe quel utilisateur Vigil, ou le code installateur du clavier (via `vigil_alarm.unlock_panel`), pour la durée réglée. Neutraliser et rétablir demandent un utilisateur qui a le droit de neutraliser (capteurs d'autoprotection : le droit supplémentaire d'autoprotection). Jusque-là, la carte n'affiche que *combien* de capteurs sont ouverts, jamais leurs noms. Quitter la liste, ou 30 secondes sans toucher, fait oublier le déverrouillage à la carte.
- **Partitions :** la carte affiche *Vigil Alarm* et la partition (ou *Toutes*) qu'elle utilise, même avec une seule partition. Avec plusieurs, des pastilles permettent de changer ; après le délai de retour (*Paramètres*, *Écran du clavier*), elle revient à la partition par défaut du clavier.
- Un utilisateur qui n'est lié à aucun clavier voit *Non lié* ; un clavier bloqué affiche *Bloqué* et ne fait rien.

## Ce que Vigil impose

- Vigil reconnaît la tablette à l'**utilisateur Home Assistant** derrière chaque appel. Home Assistant le place lui-même, il ne peut donc pas être imité en envoyant un autre texte `source`. C'est plus solide que pour un clavier ESPHome, dont les appels ne portent aucun utilisateur.
- Quoi que la carte affiche, c'est le serveur qui décide : un appel que le profil n'autorise pas est refusé et consigné (`panel_refused`). La carte n'est qu'un plus joli visage par-dessus.
- La tablette a son propre minuteur de verrouillage pour les mauvais codes, et n'est jamais traitée comme administrateur par Vigil. *Bloqué* refuse tout de cette tablette ; *Lever le verrouillage* et *Déverrouiller* fonctionnent comme pour tout clavier.
- Un téléphone éteint n'est pas une panne : pour une tablette ou un téléphone, *Surveiller si ce clavier est joignable* est désactivé par défaut, donc ni Réparation ni message. Activez-le pour une tablette qui reste au mur toute la journée.
- L'historique montre qui l'a fait, par exemple *Anna (hall-tablet)*.

## Hors ligne

La carte dit bonjour à Vigil chaque minute tant que le tableau de bord est ouvert. Si Vigil n'a rien entendu d'elle pendant 10 minutes, vous recevez une Réparation *Clavier injoignable* et un message sur vos canaux de défauts (`panel_offline`, et `panel_online` au retour), comme pour un clavier ESPHome. L'état de l'alarme ne change jamais à cause de cela. La liste des claviers affiche *Carte Vigil active* pour une tablette qui a dit bonjour.

- Seule une tablette dont la carte a dit bonjour au moins une fois est surveillée. Une tablette qui affiche la carte d'alarme propre à Home Assistant ne peut rien dire, elle n'est donc jamais signalée.
- Vigil se souvient qu'une tablette utilise la carte, de sorte qu'une tablette morte au redémarrage de Home Assistant est quand même signalée, dix minutes après le redémarrage.
- Une tablette dont l'écran est éteint et le navigateur fermé est, pour Vigil, hors ligne. Laissez une tablette murale garder le tableau de bord ouvert.

## Ce qu'il ne fait pas

- Home Assistant n'a pas de permissions par entité. L'utilisateur de la tablette peut appeler tout service qu'un utilisateur ordinaire peut appeler et lire tous les états. Vigil protège l'alarme (codes, profil, verrouillage) et la carte ne demande que ce que le profil autorise, mais l'utilisateur peut quand même quitter le tableau de bord. Ne donnez à cet utilisateur rien de plus que ce dont la tablette a besoin.
- La carte d'alarme propre à Home Assistant fonctionne toujours pour une tablette, mais elle affiche tous les modes (un mode que le profil n'autorise pas est refusé à l'appui) et n'a pas de liste de capteurs.
- La carte n'a pas de page d'info comme le clavier ESPHome ; la tablette a Home Assistant pour cela.
- Si la tablette est volée : réglez le clavier sur *Bloqué* dans Vigil, et désactivez l'utilisateur dans Home Assistant ou supprimez ses jetons d'actualisation (*Profil → Sécurité*).

## Deux comptes pour l'administrateur, et un verrou sur le navigateur

Le point faible de tout tableau de bord est le compte qui est derrière. Un administrateur n'est jamais restreint par Vigil : un administrateur qui reste connecté sur une tablette ou un téléphone donne tous les droits à cet appareil. Gardez votre **compte administrateur pour administrer uniquement**, et créez un second compte ordinaire pour l'usage quotidien (et pour la tablette, si vous en voulez une). Verrouillez le navigateur de la tablette sur le tableau de bord (un navigateur kiosque comme Fully Kiosk Browser, ou le mode kiosque de Home Assistant) pour qu'un visiteur ne puisse pas le quitter.

Deux choses protègent l'alarme d'un passant devant une tablette murale : Vigil traite le compte de la tablette comme un compte ordinaire, quoi qu'il soit dans Home Assistant (un code est toujours nécessaire pour désactiver et neutraliser), et **activer** demande aussi un code si vous activez *Code requis pour activer* dans l'onglet Paramètres. Ce réglage vaut pour tout le système : quand il est désactivé, quiconque peut appuyer sur le bouton peut activer.

## Un téléphone ou une tablette : le même registre

Une tablette au mur et le téléphone d'un colocataire sont traités de la même façon : tous deux sont une entrée de l'onglet *Claviers* liée à un compte Home Assistant (le champ *Compte Home Assistant (tablette ou téléphone)*, de préférence un compte ordinaire ; un administrateur peut aussi être choisi, avec la prudence décrite ci-dessus). Par entrée, vous réglez ce qu'elle peut faire (modes, désactivation, neutralisation, coupure du son, liste des capteurs, langue), exactement comme pour un clavier ESPHome, et la liste des capteurs suit partout les mêmes règles : masquée jusqu'à ce que le code installateur de l'entrée la déverrouille. La seule différence est la façon dont Vigil reconnaît l'appareil : un clavier ESPHome par son identifiant de clavier, un compte par l'utilisateur derrière l'appel.

- **Tout code valide fonctionne** sur un tel appareil, et l'historique montre à qui était le code, par exemple *Bob (cleo-phone)*. Pas de code, pas d'opération (là où un code est nécessaire).
- **Chaque entrée a son propre minuteur de verrouillage** : de mauvais codes sur le téléphone de Cléo verrouillent ce téléphone (par paliers, voir *Paramètres*, *Verrouillage*), pas la tablette ni personne d'autre.
- **Seuls les comptes enregistrés peuvent utiliser l'alarme.** Dès qu'un compte est enregistré, tout autre compte Home Assistant ordinaire (par exemple celui des enfants) est refusé avant que le moindre code soit examiné (événement `user_refused`, l'erreur *L'utilisateur n'est pas enregistré*), et cela ne compte pas pour un verrouillage. Les administrateurs, les automatisations, les scripts et les claviers ESPHome (appels sans utilisateur Home Assistant) ne sont pas touchés. Tant qu'aucun compte n'est enregistré, rien ne change : une mise à jour depuis une version plus ancienne ne change donc rien.
