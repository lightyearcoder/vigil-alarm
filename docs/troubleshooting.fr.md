# Mon alarme ne fait pas ce que j'attends

Ceci est une traduction de [troubleshooting.md](troubleshooting.md), traduite par Claude (une IA) et non relue par un locuteur natif. Merci de signaler les erreurs sous forme d'issue.

Cherchez ci-dessous ce que vous voyez. Pour chaque symptôme : les causes probables, où vérifier et que faire.

**Regardez toujours d'abord :**

- **Aperçu** dans le panneau : la carte *Prêt à l'emploi ?* nomme ce qui manque dans les paramètres. *Attention* nomme les capteurs dont la batterie est vide ou qui sont injoignables. *Ce que chaque mode surveille* montre quels capteurs participent à quel mode.
- **Dernier événement :** l'entité `sensor.vigil_alarm_last_event` et le journal des événements (`event.vigil_alarm_alarm_events`) disent ce qui s'est passé et pourquoi quelque chose a été refusé.
- **Attributs de l'alarme** (`alarm_control_panel.vigil_alarm`) : `open_sensors`, `bypassed_sensors`, `faults`, `problems`, `refuse_reason`.

## L'alarme ne s'active pas

| Vous voyez | Cause | Que faire |
|---|---|---|
| `refuse_reason: sensor_open` | Un capteur surveillé est ouvert (une fenêtre, par exemple). | Fermez-le, ou choisissez sur le capteur ce qui se passe s'il est ouvert à l'activation (neutraliser, attendre la fermeture, refuser). |
| `refuse_reason: sensor_unavailable` | Un capteur est injoignable (batterie vide, hors de portée). | Voyez *Attention* pour savoir lequel. Réparez-le ou neutralisez-le. |
| `refuse_reason: alarm_condition` | Une alarme d'incendie, de gaz ou d'autoprotection est active. | Supprimez la cause et désactivez d'abord. |
| `refuse_reason: not_disarmed` | L'alarme est déjà activée ou en temporisation de sortie. | Désactivez d'abord. |
| Une erreur à propos du code | Mauvais code, trop court, non autorisé pour ce mode, ou verrouillé (voir plus bas). | Vérifiez l'utilisateur dans l'onglet *Utilisateurs*. |

## L'alarme ne se déclenche pas sur une porte ouverte ou un mouvement

1. **L'alarme est-elle vraiment activée ?** Pendant la temporisation de sortie (`arming`), rien n'est encore surveillé.
2. **Le capteur est-il dans un groupe de capteurs ?** Un capteur d'intrusion sans groupe ne surveille rien. Si *Ce que chaque mode surveille* dit « aucun groupe de capteurs », créez les groupes par défaut (carte *Prêt à l'emploi ?*).
3. **Le groupe est-il actif dans ce mode ?** *Intérieur* ne vaut que pour Absent, par exemple. En Maison, un détecteur de mouvement ne déclenche jamais.
4. **Le capteur est-il neutralisé ?** Alors il figure sous `bypassed_sensors`. Une neutralisation se termine à la désactivation.
5. **Le type est-il « temporisé » ?** Alors vous avez d'abord la temporisation d'entrée (`pending`), et l'alarme ne se déclenche que si vous ne désactivez pas à temps.
6. **Y a-t-il une règle de confirmation ?** Alors l'alarme ne se déclenche que lorsque assez de capteurs différents se déclenchent dans la fenêtre de temps. Un seul capteur ne donne que l'avis « sans confirmation ».
7. **Le capteur est-il injoignable ?** Alors il ne peut pas déclencher. Voyez *Attention*.
8. **Est-ce la bonne entité ?** Dans *Outils de développement → États*, vérifiez que l'entité passe vraiment à `on` quand la porte s'ouvre.

## Pas de notification sur mon téléphone

1. Y a-t-il un **canal de notification** ? Sinon, *Prêt à l'emploi ?* le dit et propose votre téléphone.
2. Les bonnes **catégories** sont-elles activées ? Seuls les messages de ces catégories sont envoyés (alarme, temporisation d'entrée, défaut, technique).
3. Y a-t-il un **délai** ? Un canal d'escalade avec un délai de 30 secondes ne notifie qu'après 30 secondes, et pas si vous désactivez ou acquittez avant.
4. Utilisez le **bouton de test** du canal. Si le test n'arrive pas, le problème vient de Home Assistant ou de l'application, pas de l'alarme : vérifiez l'autorisation de notification de l'application sur votre téléphone.
5. Le **service** est-il le bon ? Ce doit être un service `notify.` existant.

## La sirène ne retentit pas

1. Une sirène est-elle configurée, et retentit-elle pour *cette cause* (intrusion, incendie, gaz, autoprotection, défaut) ?
2. Essayez l'action `vigil_alarm.test_siren`. Si elle ne retentit pas, le problème vient de l'entité elle-même (injoignable, batterie vide).
3. La sirène a-t-elle été **coupée** avec `vigil_alarm.silence` ? Alors l'alarme reste active mais la sirène se tait.
4. La **durée maximale** est-elle écoulée ? La sirène s'arrête d'elle-même ensuite.

## Mon code est refusé

- **Trop court :** la longueur minimale est dans *Paramètres* (4 à 12 caractères).
- **Verrouillé :** après quelques mauvais codes, Vigil verrouille cet endroit par paliers (par défaut 5, puis 15, puis 60 minutes), y compris pour le bon code. Patientez un moment ; le journal des événements montre `code_locked`. S'il montre `code_locked_permanent`, le clavier reste fermé jusqu'à ce qu'un administrateur appuie sur *Lever le verrouillage* sous Claviers. Les valeurs sont sous *Paramètres*, *Verrouillage*.
- **Non autorisé :** l'utilisateur ne peut utiliser que certains modes. Vérifiez *Modes autorisés*. Désactiver fonctionne toujours avec un code valide.

## Fausses alarmes

- Donnez aux portes le type **temporisé** avec une temporisation d'entrée, pour pouvoir désactiver à temps.
- Laissez un détecteur de mouvement ne surveiller qu'en Absent (groupe *Intérieur*).
- Utilisez une **règle de confirmation** : une alarme seulement si deux détecteurs de mouvement se déclenchent en une minute.
- Pour une notification, consultez le journal des événements pour voir quel capteur c'était.

## Pas de notifications de batterie ou d'autoprotection

- Le capteur a besoin d'un **capteur de batterie**. *Prêt à l'emploi ?* nomme les capteurs qui n'en ont pas. Un appareil qui signale seulement « batterie faible » (marche/arrêt) convient aussi.
- Si l'appareil a un **capteur d'autoprotection**, indiquez-le sur le capteur. La carte nomme les capteurs d'autoprotection qui ne sont reliés à rien.

## Les entités ne portent pas les noms attendus

Les identifiants d'entités de Vigil se terminent toujours par le nom anglais, même quand Home Assistant est réglé sur une autre langue (par exemple `binary_sensor.vigil_alarm_intrusion_alarm`). Ce que vous voyez dans l'interface suit votre propre langue. Vérifiez les vrais noms sous *Paramètres → Appareils et services → Vigil Alarm*. Si vous venez d'une version plus ancienne, mettez à jour vos automatisations et tableaux de bord avec les nouveaux identifiants (voir les notes de version).

## Le panneau est vide

Rechargez le navigateur en forçant (Ctrl+F5) et vérifiez que l'intégration fonctionne sous *Appareils et services*. Sinon, regardez le journal (*Paramètres → Système → Journaux*, cherchez `vigil`).

## Cela ne fonctionne toujours pas ?

Téléchargez les diagnostics (*Appareils et services → Vigil Alarm → ⋮ → Télécharger les diagnostics*), qui ne contiennent ni codes ni noms de personnes, et signalez-le sur GitHub (voir l'onglet *À propos*).

## Je reçois sans cesse un rappel de test de sirène

Le rappel se répète jusqu'à ce qu'un test soit fait. Appuyez sur *Tester la sirène* dans le message, utilisez *Tester la sirène maintenant* dans l'onglet Aperçu, ou appelez `vigil_alarm.test_siren`. Pour arrêter les rappels, réglez l'intervalle sous *Paramètres* sur 0.

## Le heartbeat échoue

La carte *Heartbeat* de l'onglet Aperçu nomme la raison : *pas de connexion* (Home Assistant n'atteint pas internet ou l'adresse est fausse), *pas de réponse en 10 secondes*, ou *HTTP 404* et similaire (le service ne connaît pas l'adresse ; copiez-la de nouveau). Corrigez-la sous *Paramètres* et cliquez sur *Tester maintenant*.
