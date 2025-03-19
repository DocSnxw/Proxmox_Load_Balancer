import os
os.system("pip3 install -r requirements.txt")

from proxmoxer import ProxmoxAPI
import time
import logging
from typing import Dict, List
import sys
from colorama import init, Fore, Style
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# Configuration du script a partir des variables d'environnement
PROXMOX_HOST = os.getenv('PROXMOX_HOST')
PROXMOX_USER = os.getenv('PROXMOX_USER')
PROXMOX_PASSWORD = os.getenv('PROXMOX_PASSWORD')
CPU_THRESHOLD = int(os.getenv('CPU_THRESHOLD'))
RAM_THRESHOLD = int(os.getenv('RAM_THRESHOLD'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL'))

# Valider la configuration
if not all([PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASSWORD]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

# Setup login
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('load_balancer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DashboardUI:
    def __init__(self):
        self.nodes_stats = {}
        self.last_update = None
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def get_color(self, value):
        if value > 80:
            return Fore.RED
        elif value > 60:
            return Fore.YELLOW
        return Fore.GREEN
        
    def draw_header(self):
        header = """
 _______                                 __       __                            __                                 __        _______             __                                                   
|       \                               |  \     /  \                          |  \                               |  \      |       \           |  \                                                  
| $$$$$$$\  ______    ______   __    __ | $$\   /  $$  ______   __    __       | $$       ______    ______    ____| $$      | $$$$$$$\  ______  | $$  ______   _______    _______   ______    ______  
| $$__/ $$ /      \  /      \ |  \  /  \| $$$\ /  $$$ /      \ |  \  /  \      | $$      /      \  |      \  /      $$      | $$__/ $$ |      \ | $$ |      \ |       \  /       \ /      \  /      \ 
| $$    $$|  $$$$$$\|  $$$$$$\ \$$\/  $$| $$$$\  $$$$|  $$$$$$\ \$$\/  $$      | $$     |  $$$$$$\  \$$$$$$\|  $$$$$$$      | $$    $$  \$$$$$$\| $$  \$$$$$$\| $$$$$$$\|  $$$$$$$|  $$$$$$\|  $$$$$$\\
| $$$$$$$ | $$   \$$| $$  | $$  >$$  $$ | $$\$$ $$ $$| $$  | $$  >$$  $$       | $$     | $$  | $$ /      $$| $$  | $$      | $$$$$$$\ /      $$| $$ /      $$| $$  | $$| $$      | $$    $$| $$   \$$
| $$      | $$      | $$__/ $$ /  $$$$\ | $$ \$$$| $$| $$__/ $$ /  $$$$\       | $$_____| $$__/ $$|  $$$$$$$| $$__| $$      | $$__/ $$|  $$$$$$$| $$|  $$$$$$$| $$  | $$| $$_____ | $$$$$$$$| $$      
| $$      | $$       \$$    $$|  $$ \$$\| $$  \$ | $$ \$$    $$|  $$ \$$\      | $$     \\$$    $$ \$$    $$ \$$    $$      | $$    $$ \$$    $$| $$ \$$    $$| $$  | $$ \$$     \ \$$     \| $$      
 \$$       \$$        \$$$$$$  \$$   \$$ \$$      \$$  \$$$$$$  \$$   \$$       \$$$$$$$$ \$$$$$$   \$$$$$$$  \$$$$$$$       \$$$$$$$   \$$$$$$$ \$$  \$$$$$$$ \$$   \$$  \$$$$$$$  \$$$$$$$ \$$      
"""
        print(Fore.CYAN + header + Style.RESET_ALL)
        if self.last_update:
            print(f"Last update: {self.last_update.strftime('%H:%M:%S')}")
        print("=" * 140 + "\n")
        
    def update_stats(self, stats):
        self.nodes_stats = stats
        self.last_update = datetime.now()
        
    def draw(self):
        self.clear_screen()
        self.draw_header()
        
        if not self.nodes_stats:
            print(Fore.YELLOW + "Waiting for data..." + Style.RESET_ALL)
            return
            
        for node, stats in self.nodes_stats.items():
            print(f"\n{Fore.BLUE}Node: {node} (CPU Capacity: {stats['cpu_capacity']:.1f}x){Style.RESET_ALL}")
            print("─" * 70)
            
            cpu_color = self.get_color(stats['raw_cpu'])
            mem_color = self.get_color(stats['memory'])
            
            print(f"Raw CPU Usage: {cpu_color}{stats['raw_cpu']:.1f}%{Style.RESET_ALL}")
            print(f"Normalized CPU: {cpu_color}{stats['cpu']:.1f}%{Style.RESET_ALL}")
            print(f"RAM Usage: {mem_color}{stats['memory']:.1f}%{Style.RESET_ALL}")
            
            if 'vms' in stats:
                print("\nRunning VMs:")
                if stats['vms']:
                    for vm in stats['vms']:
                        print(f"  • {Fore.GREEN}{vm['name']}{Style.RESET_ALL} (ID: {vm['vmid']})")
                else:
                    print("  No running VMs")
            print("─" * 70)

class ProxmoxLoadBalancer:
    def __init__(self):
        logging.info("Initializing Proxmox Load Balancer...")
        self.proxmox = ProxmoxAPI(
            host=PROXMOX_HOST,
            user=PROXMOX_USER,
            password=PROXMOX_PASSWORD,
            verify_ssl=False,
            port=8006,
            service='PVE'
        )
        self.ui = DashboardUI()
        self.migration_history = {}  # Garder en mémoire les dernières migrations effectuées avec le script
        self.migration_cooldown = 300  # Cooldown de 5 minutes entre les migrations d'une même VM
        self.balanced_threshold = 2  # Différence maximale de VM entre chaque nodes
        self.load_difference_threshold = 15  # DIfférence maximale de charge entre les nodes
        logging.info(f"Successfully connected to Proxmox server at {PROXMOX_HOST}")
        # Définition des capacités relatives des CPUs pour chaque nœud (1.0 = référence)

        # Changer les valeurs ci-dessous pour correspondre à votre configuration

        self.node_cpu_capacity = {
            'pve': 1.0,
            'pve2': 1.0,
            'pve3': 0.75
        }

    def get_node_stats(self) -> Dict:
        """Get current CPU and RAM usage for all nodes"""
        logging.info("Starting to fetch node statistics...")
        nodes_stats = {}
        for node in self.proxmox.nodes.get():
            node_name = node['node']
            logging.info(f"Fetching stats for node: {node_name}")
            status = self.proxmox.nodes(node_name).status.get()
            cpu_info = self.proxmox.nodes(node_name).execute('cat /proc/cpuinfo')
            
            # Calculer la charge CPU normalisée en fonction de la capacité du node
            cpu_capacity = self.node_cpu_capacity.get(node_name, 1.0)
            raw_cpu_usage = status['cpu'] * 100
            normalized_cpu_usage = raw_cpu_usage / cpu_capacity
            
            memory_usage = (status['memory']['used'] / status['memory']['total']) * 100
            
            # Charger les VMs en cours d'exécution pour chaque node
            vms = []
            for vm in self.proxmox.nodes(node_name).qemu.get():
                if vm['status'] == 'running':
                    vms.append({
                        'vmid': vm['vmid'],
                        'name': vm.get('name', f"VM{vm['vmid']}"),
                        'memory': vm['maxmem'],
                        'cpu': vm.get('cpu', 1)  # Nombre de vCPUs
                    })
            
            nodes_stats[node_name] = {
                'cpu': normalized_cpu_usage,
                'raw_cpu': raw_cpu_usage,
                'cpu_capacity': cpu_capacity,
                'memory': memory_usage,
                'total_memory': status['memory']['total'],
                'vms': vms
            }
            logging.info(f"Node {node_name} stats - CPU: {normalized_cpu_usage:.1f}%, Memory: {memory_usage:.1f}%")
        return nodes_stats

    def get_vms_by_node(self) -> Dict:
        """Get all VMs and their resources by node"""
        logging.info("Starting to fetch VM information...")
        vms = {}
        for node in self.proxmox.nodes.get():
            node_name = node['node']
            logging.info(f"Fetching VMs for node: {node_name}")
            vms[node_name] = []
            for vm in self.proxmox.nodes(node_name).qemu.get():
                if vm['status'] == 'running':
                    vm_info = {
                        'vmid': vm['vmid'],
                        'name': vm.get('name', f"VM{vm['vmid']}"),
                        'memory': vm['maxmem']
                    }
                    vms[node_name].append(vm_info)
                    logging.info(f"Found running VM: {vm_info['name']} (ID: {vm_info['vmid']}) on node {node_name}")
        return vms

    def can_host_vm(self, vm_info: Dict, node_stats: Dict) -> bool:
        """Check if a node can host a VM based on available resources and CPU capacity"""
        # Vérifier la mémoire
        required_memory = vm_info.get('memory', 0) / (1024 * 1024 * 1024)
        available_memory = (node_stats['total_memory'] * (1 - node_stats['memory']/100)) / (1024 * 1024 * 1024)
        
        # Vérifier la capacité CPU
        vm_cpu_count = vm_info.get('cpu', 1)
        cpu_headroom = 100 - node_stats['raw_cpu']
        cpu_capacity_available = cpu_headroom * node_stats['cpu_capacity']
        
        return (available_memory >= required_memory and 
                cpu_capacity_available >= (vm_cpu_count * 25))  # 25% par vCPU comme marge

    def get_vm_score(self, vm_info: Dict) -> float:
        """Calculate migration priority score for a VM"""
        memory_gb = vm_info.get('memory', 0) / (1024 * 1024 * 1024)
        
        # Check if VM was recently migrated
        last_migration = self.migration_history.get(vm_info['vmid'], 0)
        time_since_migration = time.time() - last_migration
        
        if time_since_migration < self.migration_cooldown:
            return 0
            
        return 1 / memory_gb if memory_gb > 0 else 0

    def get_target_node_score(self, node_stats: Dict) -> float:
        """Calculate score for target node suitability"""
        cpu_headroom = 100 - node_stats['cpu']
        memory_headroom = 100 - node_stats['memory']
        return (cpu_headroom + memory_headroom) / 2

    def migrate_vm(self, vmid: int, source_node: str, target_node: str) -> bool:
        """Migrate a VM from source to target node"""
        try:
            # Vérifier si la VM à été migrée il y a moins de 5 minutes
            if vmid in self.migration_history:
                last_migration = self.migration_history[vmid]
                if time.time() - last_migration < self.migration_cooldown:
                    logging.info(f"Skipping VM {vmid}: too soon since last migration")
                    return False

            # Faire la migration
            self.proxmox.nodes(source_node).qemu(vmid).migrate.post(
                target=target_node,
                online=1
            )
            
            # Mettre à jour l'historique des migrations
            self.migration_history[vmid] = time.time()
            logging.info(f"Started migration of VM {vmid} from {source_node} to {target_node}")
            return True
            
        except Exception as e:
            logging.error(f"Migration failed: {str(e)}")
            return False

    def get_vm_distribution(self, nodes_stats: Dict) -> Dict[str, int]:
        """Get number of VMs per node"""
        return {node: len(stats['vms']) for node, stats in nodes_stats.items()}
        
    def get_node_load(self, node_stats: Dict) -> float:
        """Calculate combined load score for a node taking into account CPU capacity"""
        # CPU et RAM sont pondérés différemment
        cpu_weight = 0.6  # CPU compte pour 60%
        ram_weight = 0.4  # RAM compte pour 40%
        return (node_stats['cpu'] * cpu_weight) + (node_stats['memory'] * ram_weight)
        
    def needs_rebalancing(self, nodes_stats: Dict) -> bool:
        """Check if cluster needs rebalancing based on load distribution"""
        if not nodes_stats:
            return False
            
        loads = [self.get_node_load(stats) for stats in nodes_stats.values()]
        min_load = min(loads)
        max_load = max(loads)
        
        return (max_load - min_load) > self.load_difference_threshold

    def balance_load(self):
        """Main balancing logic"""
        nodes_stats = self.get_node_stats()
        
        if not self.needs_rebalancing(nodes_stats):
            logging.info("Load is distributed evenly across nodes")
            return

        # Calculer la charge de chaque node
        node_loads = {
            node: self.get_node_load(stats)
            for node, stats in nodes_stats.items()
        }

        # Trier les nodes par charge décroissante
        sorted_nodes = sorted(node_loads.items(), key=lambda x: x[1], reverse=True)
        
        # Identifier les nodes surchargés et sous-chargés
        source_nodes = []
        target_nodes = []
        avg_load = sum(node_loads.values()) / len(node_loads)
        
        for node, load in sorted_nodes:
            if load > avg_load + (self.load_difference_threshold / 2):
                source_nodes.append(node)
            elif load < avg_load - (self.load_difference_threshold / 2):
                target_nodes.append(node)

        # Si tous les nodes sont équilibrés, ne rien faire
        for source_node in source_nodes:
            source_vms = nodes_stats[source_node]['vms']
            
            # Trier les VMs par score de priorité
            scored_vms = [(vm, self.get_vm_score(vm)) for vm in source_vms]
            scored_vms.sort(key=lambda x: x[1], reverse=True)

            for target_node in target_nodes:
                current_difference = node_loads[source_node] - node_loads[target_node]
                
                if current_difference <= self.load_difference_threshold:
                    break

                for vm, score in scored_vms:
                    if score == 0: 
                        continue
                        
                    if self.can_host_vm(vm, nodes_stats[target_node]):
                        if self.migrate_vm(vm['vmid'], source_node, target_node):
                            vm_impact = 10  # Impact de charge arbitraire pour chaque VM migrée
                            node_loads[source_node] -= vm_impact
                            node_loads[target_node] += vm_impact
                            time.sleep(5)  # Attendre quelques secondes entre les migrations
                            break

    def run(self):
        """Main loop"""
        print(Fore.GREEN + "Starting Proxmox Load Balancer (Load Distribution Mode)..." + Style.RESET_ALL)
        try:
            while True:
                try:
                    nodes_stats = self.get_node_stats()
                    self.ui.update_stats(nodes_stats)
                    self.ui.draw()
                    
                    # Afficher la distribution de charge actuelle
                    print("\nLoad Distribution:")
                    for node, stats in nodes_stats.items():
                        load = self.get_node_load(stats)
                        load_color = self.ui.get_color(load)
                        print(f"{Fore.BLUE}{node}{Style.RESET_ALL}: {load_color}{load:.1f}%{Style.RESET_ALL} load")
                    
                    self.balance_load()
                    time.sleep(CHECK_INTERVAL)
                except Exception as e:
                    logging.error(f"Error: {str(e)}")
                    time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            self.ui.clear_screen()
            print(Fore.YELLOW + "\nShutting down gracefully..." + Style.RESET_ALL)

if __name__ == "__main__":
    try:
        balancer = ProxmoxLoadBalancer()
        balancer.run()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nExiting..." + Style.RESET_ALL)
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        print(Fore.RED + f"\nFatal error: {str(e)}" + Style.RESET_ALL)
