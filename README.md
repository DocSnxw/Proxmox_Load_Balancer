# Proxmox Load Balancer

Un équilibreur de charge automatique pour clusters Proxmox qui optimise la distribution des VMs en fonction de la charge CPU et mémoire.

## 🌟 Fonctionnalités

- Surveillance en temps réel de la charge CPU et mémoire
- Migration automatique des VMs pour équilibrer la charge
- Interface utilisateur en console avec indicateurs colorés
- Support pour des nœuds avec différentes capacités CPU
- Protection contre les migrations trop fréquentes
- Configuration via variables d'environnement

## 📋 Prérequis

- Python 3.8+
- Accès administrateur à un cluster Proxmox
- Pip (gestionnaire de paquets Python)

## 🚀 Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/DocSnxw/proxmox-load-balancer.git
cd proxmox-load-balancer
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez vos variables d'environnement dans le fichier `.env` :
```properties
# Proxmox credentials
PROXMOX_HOST=votre_host
PROXMOX_USER=votre_user
PROXMOX_PASSWORD=votre_password

# Optional settings
CPU_THRESHOLD=80
RAM_THRESHOLD=80
CHECK_INTERVAL=15
```

## 💻 Utilisation

Lancez le script :
```bash
python proxmox_balancer.py
```

## ⚙️ Configuration

### Configuration des nœuds
Modifiez les capacités relatives des CPUs dans `proxmox_balancer.py` :
```python
self.node_cpu_capacity = {
    'pve': 1.0,    # Node de référence
    'pve2': 1.0,   # Même puissance que pve
    'pve3': 0.75   # 25% moins puissant que pve
}
```

### Paramètres ajustables
- `CPU_THRESHOLD`: Seuil de charge CPU (%)
- `RAM_THRESHOLD`: Seuil de charge mémoire (%)
- `CHECK_INTERVAL`: Intervalle de vérification (secondes)
- `migration_cooldown`: Temps d'attente entre les migrations (secondes)
- `load_difference_threshold`: Différence de charge maximale acceptable (%)

## 🛡️ Sécurité

- Les identifiants sensibles sont stockés dans le fichier `.env`
- Vérification SSL désactivée par défaut (à activer en production)
- Journal des opérations disponible dans `load_balancer.log`

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some Amazing Features'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🔧 Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.

## ⚠️ Avertissement

Ce script est fourni tel quel, sans garantie. Testez-le dans un environnement de développement avant de l'utiliser en production.
