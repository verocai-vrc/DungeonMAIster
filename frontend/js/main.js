let ws;
let currentCharacterData = null;
let currentEditInventory = [];
let lastAppliedRace = null;

// --- SISTEMA DE TABS ---
function switchTab(tabId) {
    ['sheet', 'inventory', 'spells', 'system'].forEach(id => {
        document.getElementById(`tab-${id}`).classList.add('hidden');
        document.getElementById(`btn-${id}`).classList.remove('border-blue-500', 'text-blue-400');
        document.getElementById(`btn-${id}`).classList.add('border-transparent', 'text-gray-400');
    });
    document.getElementById(`tab-${tabId}`).classList.remove('hidden');
    document.getElementById(`btn-${tabId}`).classList.add('border-blue-500', 'text-blue-400');
    document.getElementById(`btn-${tabId}`).classList.remove('border-transparent', 'text-gray-400');
}

// --- WEBSOCKETS (CHAT) ---
function connectWS() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        appendMessage('Sistema', 'Já estás conectado ao servidor.');
        return;
    }
    ws = new WebSocket("ws://localhost:8000/ws");
    ws.onopen = () => {
        document.getElementById('ws-status').textContent = 'Conectado';
        document.getElementById('ws-status').className = 'text-sm text-green-400 font-bold';
        appendMessage('Sistema', 'Conexão estabelecida com o servidor DungeonMAIster.');
    };
    ws.onmessage = (event) => appendMessage('Mestre', event.data);
    ws.onclose = () => {
        document.getElementById('ws-status').textContent = 'Desconectado';
        document.getElementById('ws-status').className = 'text-sm text-red-400 font-bold';
        appendMessage('Sistema', 'A conexão com o servidor foi perdida.');
    };
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("Por favor, conecta-te ao Mestre IA primeiro na aba 'Sistema'."); return;
    }
    appendMessage('Jogador', message);
    ws.send(message);
    input.value = '';
}

function handleKeyPress(event) { if (event.key === 'Enter') sendMessage(); }

function appendMessage(sender, text) {
    const history = document.getElementById('chat-history');
    const div = document.createElement('div');
    const isPlayer = sender === 'Jogador';
    const isSystem = sender === 'Sistema';
    
    if (!isPlayer && !isSystem) {
        const rollRegex = /\[REQUEST_ROLL:(.*?)\]/g;
        text = text.replace(rollRegex, (match, expr) => {
            return `<div class="mt-4 border-t border-gray-700 pt-3"><button onclick="sendRoll('${expr}')" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded font-bold shadow-md transition w-full flex justify-center items-center gap-2">🎲 Rolar Teste (${expr})</button></div>`;
        });
    }

    div.className = `p-3 rounded-lg w-max max-w-[85%] ${isPlayer ? 'bg-blue-900/40 text-blue-100 self-end ml-auto border border-blue-800/50' : (isSystem ? 'bg-gray-800 text-gray-400 self-center text-sm' : 'bg-gray-800 text-gray-200 self-start border border-gray-700')}`;
    div.innerHTML = `<span class="font-bold block text-xs opacity-75 mb-1 ${isPlayer ? 'text-blue-300' : (isSystem ? 'text-gray-500' : 'text-yellow-400')}">${sender}</span><span>${text}</span>`;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

function sendRoll(expr) {
    if (!ws || ws.readyState !== WebSocket.OPEN) { alert("Por favor, conecta-te ao Mestre IA."); return; }
    ws.send(`/roll ${expr}`);
}

function quickRoll(name, isAttribute = false, mod = 0) {
    let expr = '1d20';
    if (isAttribute) { expr = `1d20${mod >= 0 ? '+' + mod : mod}`; } 
    else {
        const desc = (dndRules && dndRules.descriptions && dndRules.descriptions[name]) ? dndRules.descriptions[name] : "";
        const match = desc.match(/(\d+d\d+(?:\s*[+-]\s*\d+)?)/);
        expr = match ? match[1].replace(/\s/g, '') : '1d20';
    }
    const input = document.getElementById('chat-input');
    input.value = `/roll ${expr}`;
    input.focus();
}

function renderTooltipItem(name) {
    const desc = (dndRules && dndRules.descriptions && dndRules.descriptions[name]) ? dndRules.descriptions[name] : "Descrição não definida.";
    return `<li class="relative group w-max list-none mb-1">
        <span onclick="quickRoll('${name.replace(/'/g, "\\'")}', false)" class="inline-flex items-center gap-2 cursor-pointer"><span class="text-blue-500 text-xs hover:text-blue-400">✦</span><span class="border-b border-dashed border-gray-500 hover:text-blue-300 transition">${name}</span></span>
        <div class="absolute left-6 top-full mt-1 hidden group-hover:block w-64 bg-gray-950 text-gray-300 text-xs rounded p-3 shadow-xl border border-gray-700 z-[60] pointer-events-none">
            <strong class="text-blue-400 block mb-1 border-b border-gray-700 pb-1">${name}</strong>${desc}
        </div>
    </li>`;
}

async function loadCharacter() {
    try {
        const response = await fetch("http://localhost:8000/api/character");
        if (!response.ok) throw new Error("Erro de rede");
        const data = await response.json();
        currentCharacterData = data;
        
        document.getElementById('char-name').textContent = data.name;
        document.getElementById('char-race').textContent = data.race;
        document.getElementById('char-class').textContent = data.character_class;
        document.getElementById('char-level').textContent = data.level;
        document.getElementById('char-xp').textContent = data.xp !== undefined ? data.xp : 0;
        document.getElementById('char-location').textContent = data.location;
        document.getElementById('char-hp').textContent = `${data.current_hp} / ${data.max_hp}`;
        document.getElementById('char-ac').textContent = data.armor_class;

        const attrDiv = document.getElementById('char-attributes');
        attrDiv.innerHTML = ''; 
        const attrs = [
            { name: "FOR", val: data.attributes.strength, mod: data.attributes.str_mod },
            { name: "DES", val: data.attributes.dexterity, mod: data.attributes.dex_mod },
            { name: "CON", val: data.attributes.constitution, mod: data.attributes.con_mod },
            { name: "INT", val: data.attributes.intelligence, mod: data.attributes.int_mod },
            { name: "SAB", val: data.attributes.wisdom, mod: data.attributes.wis_mod },
            { name: "CAR", val: data.attributes.charisma, mod: data.attributes.cha_mod }
        ];
        attrs.forEach(a => {
            attrDiv.innerHTML += `<div onclick="quickRoll('${a.name}', true, ${a.mod})" class="bg-gray-800 p-3 border border-gray-700 rounded flex justify-between items-center cursor-pointer hover:bg-gray-700 transition" title="Rolar Teste de ${a.name}"><span class="font-bold text-gray-400 pointer-events-none">${a.name}</span><div class="text-right pointer-events-none"><span class="text-xl font-semibold text-gray-200">${a.val}</span><span class="text-sm text-gray-500 ml-2">(${a.mod >= 0 ? '+'+a.mod : a.mod})</span></div></div>`;
        });

        const invUl = document.getElementById('char-inventory');
        invUl.innerHTML = data.inventory.map(item => renderTooltipItem(item)).join('');
        if(data.inventory.length === 0) invUl.innerHTML = '<li class="text-gray-500 italic text-sm p-1 list-none">Vazio.</li>';

        const featsUl = document.getElementById('char-features');
        featsUl.innerHTML = data.features.map(feat => renderTooltipItem(feat)).join('');
        if(data.features.length === 0) featsUl.innerHTML = '<li class="text-gray-500 italic list-none">Nenhuma característica.</li>';

        switchTab('sheet');
    } catch (error) { console.error(error); alert("Erro ao carregar a ficha. Verifica o backend."); }
}

let dndRules = null;
async function fetchRules() {
    try {
        const response = await fetch("http://localhost:8000/api/rules");
        if (response.ok) {
            dndRules = await response.json();
            const raceSelect = document.getElementById('edit-race');
            const classSelect = document.getElementById('edit-class');
            Object.keys(dndRules.races).forEach(race => { raceSelect.add(new Option(race, race)); });
            Object.keys(dndRules.classes).forEach(cls => { classSelect.add(new Option(cls, cls)); });

            const inventorySelect = document.getElementById('add-inventory-select');
            if (dndRules.equipment && dndRules.equipment.length > 0) {
                dndRules.equipment.forEach(item => { inventorySelect.add(new Option(item, item)); });
            }

            const spellsContainer = document.getElementById('spells-container');
            spellsContainer.innerHTML = '';
            if (dndRules.spells && Object.keys(dndRules.spells).length > 0) {
                Object.keys(dndRules.spells).forEach(level => {
                    let html = `<div class="bg-gray-800 p-3 rounded border border-gray-700 shadow-sm"><h4 class="text-blue-400 font-bold mb-2">Círculo ${level}</h4><ul class="text-gray-300 text-sm space-y-1">`;
                    dndRules.spells[level].forEach(spell => { html += renderTooltipItem(spell); });
                    html += `</ul></div>`;
                    spellsContainer.innerHTML += html;
                });
            } else { spellsContainer.innerHTML = '<div class="text-gray-500 italic text-sm">Nenhuma magia encontrada.</div>'; }
        }
    } catch (error) { console.error("Erro ao carregar as regras:", error); }
}
window.addEventListener('DOMContentLoaded', fetchRules);

function updateInventoryUI() {
    const list = document.getElementById('edit-inventory-list');
    list.innerHTML = currentEditInventory.map((item, index) => 
        `<li class="flex justify-between items-center bg-gray-800 p-1 px-2 rounded"><span>${item}</span><button type="button" onclick="removeInventoryItem(${index})" class="text-red-400 hover:text-red-300 font-bold px-2 text-lg leading-none">&times;</button></li>`
    ).join('');
    if (currentEditInventory.length === 0) list.innerHTML = '<li class="text-gray-500 italic text-sm p-1">Inventário vazio.</li>';
}

function addInventoryItem() {
    const item = document.getElementById('add-inventory-select').value;
    if (item) { currentEditInventory.push(item); updateInventoryUI(); updateAutoFeatures(); }
}
function removeInventoryItem(index) { currentEditInventory.splice(index, 1); updateInventoryUI(); updateAutoFeatures(); }

function updateAutoFeatures() {
    if (!dndRules) return;
    const race = document.getElementById('edit-race').value;
    const cls = document.getElementById('edit-class').value;
    const lvl = parseInt(document.getElementById('edit-level').value) || 1;
    const attrKeys = { "strength": "str", "dexterity": "dex", "constitution": "con", "intelligence": "int", "wisdom": "wis", "charisma": "cha" };
    let autoFeats = [];
    
    const raceData = dndRules.races[race];
    if (raceData) {
        if (lastAppliedRace !== race) {
            if (lastAppliedRace && dndRules.races[lastAppliedRace] && dndRules.races[lastAppliedRace].attributes) {
                const oldBonuses = dndRules.races[lastAppliedRace].attributes;
                Object.keys(oldBonuses).forEach(k => {
                    const inp = document.getElementById(`edit-${attrKeys[k]}`);
                    if (inp) inp.value = parseInt(inp.value) - oldBonuses[k];
                });
            }
            if (raceData.attributes) {
                Object.keys(raceData.attributes).forEach(k => {
                    const inp = document.getElementById(`edit-${attrKeys[k]}`);
                    if (inp) inp.value = parseInt(inp.value) + raceData.attributes[k];
                });
            }
            lastAppliedRace = race;
        }
        if (raceData.features) autoFeats.push(...raceData.features);
    }
    
    const classData = dndRules.classes[cls];
    if (classData) {
        if (classData.proficiencies) autoFeats.push(`Perícias: ${classData.proficiencies.join(", ")}`);
        if (classData.features) {
            for (let i = 1; i <= lvl; i++) {
                if (classData.features[i]) autoFeats.push(...classData.features[i]);
            }
        }
    }
    if (lvl > 3) autoFeats.push(`Mais habilidades da Classe ${cls} nível ${lvl}`);
    document.getElementById('edit-features').value = autoFeats.join(", ");
    const con = parseInt(document.getElementById('edit-con').value) || 10;
    const conMod = Math.floor((con - 10) / 2);
    const hitDie = classData ? classData.hit_dice : 8;
    let maxHp = hitDie + conMod;
    if (lvl > 1) { const avgHitDie = Math.floor(hitDie / 2) + 1; maxHp += (lvl - 1) * Math.max(1, (avgHitDie + conMod)); }
    document.getElementById('edit-max-hp').value = maxHp;
    const currentHpInput = document.getElementById('edit-current-hp');
    if (parseInt(currentHpInput.value) > maxHp || currentHpInput.value === "10") { currentHpInput.value = maxHp; }

    const dex = parseInt(document.getElementById('edit-dex').value) || 10;
    const dexMod = Math.floor((dex - 10) / 2);
    let baseAC = 10 + dexMod;
    let bestArmorAC = 0; let hasShield = false;
    if (dndRules.armor) {
        currentEditInventory.forEach(item => {
            const armorData = dndRules.armor[item];
            if (armorData) {
                if (armorData.type === 'shield') { hasShield = true; } 
                else {
                    let calcAC = armorData.base;
                    if (armorData.type === 'light') calcAC += dexMod;
                    else if (armorData.type === 'medium') calcAC += Math.min(dexMod, 2);
                    if (calcAC > bestArmorAC) bestArmorAC = calcAC;
                }
            }
        });
    }
    let finalAC = bestArmorAC > 0 ? bestArmorAC : baseAC;
    if (hasShield) finalAC += 2;
    document.getElementById('edit-ac').value = finalAC;
}

function openEditModal(isNew) {
    const title = document.getElementById('modal-title');
    if (isNew || !currentCharacterData) {
        title.textContent = "Nova Ficha";
        ['edit-name','edit-inventory','edit-location'].forEach(id => document.getElementById(id).value = id === 'edit-location' ? "Desconhecido" : "");
        ['edit-race','edit-class'].forEach(id => document.getElementById(id).selectedIndex = 0);
        ['edit-level','edit-max-hp','edit-current-hp','edit-ac','edit-str','edit-dex','edit-con','edit-int','edit-wis','edit-cha'].forEach(id => document.getElementById(id).value = (id === 'edit-level') ? "1" : "10");
        currentEditInventory = []; updateInventoryUI(); lastAppliedRace = null; updateAutoFeatures();
    } else {
        title.textContent = "Editar Ficha";
        const d = currentCharacterData;
        document.getElementById('edit-name').value = d.name; document.getElementById('edit-race').value = d.race; document.getElementById('edit-class').value = d.character_class;
        document.getElementById('edit-level').value = d.level; document.getElementById('edit-xp').value = d.xp !== undefined ? d.xp : 0; document.getElementById('edit-location').value = d.location;
        document.getElementById('edit-max-hp').value = d.max_hp; document.getElementById('edit-current-hp').value = d.current_hp; document.getElementById('edit-ac').value = d.armor_class;
        document.getElementById('edit-str').value = d.attributes.strength; document.getElementById('edit-dex').value = d.attributes.dexterity; document.getElementById('edit-con').value = d.attributes.constitution;
        document.getElementById('edit-int').value = d.attributes.intelligence; document.getElementById('edit-wis').value = d.attributes.wisdom; document.getElementById('edit-cha').value = d.attributes.charisma;
        currentEditInventory = [...d.inventory]; updateInventoryUI(); lastAppliedRace = d.race; document.getElementById('edit-features').value = d.features.join(", ");
    }
    document.getElementById('char-modal').classList.remove('hidden');
}

function closeEditModal() { document.getElementById('char-modal').classList.add('hidden'); }

async function saveCharacter() {
    const payload = {
        name: document.getElementById('edit-name').value || "Herói", race: document.getElementById('edit-race').value || "Humano",
        character_class: document.getElementById('edit-class').value || "Aventureiro", level: parseInt(document.getElementById('edit-level').value) || 1, xp: parseInt(document.getElementById('edit-xp').value) || 0,
        location: document.getElementById('edit-location').value || "Desconhecido", max_hp: parseInt(document.getElementById('edit-max-hp').value) || 10,
        current_hp: parseInt(document.getElementById('edit-current-hp').value) || 10, armor_class: parseInt(document.getElementById('edit-ac').value) || 10,
        inventory: currentEditInventory, features: document.getElementById('edit-features').value.split(',').map(i => i.trim()).filter(i => i !== ''),
        attributes: { strength: parseInt(document.getElementById('edit-str').value) || 10, dexterity: parseInt(document.getElementById('edit-dex').value) || 10, constitution: parseInt(document.getElementById('edit-con').value) || 10, intelligence: parseInt(document.getElementById('edit-int').value) || 10, wisdom: parseInt(document.getElementById('edit-wis').value) || 10, charisma: parseInt(document.getElementById('edit-cha').value) || 10 }
    };
    try {
        const res = await fetch("http://localhost:8000/api/character", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        if (!res.ok) throw new Error();
        closeEditModal(); loadCharacter(); appendMessage('Sistema', 'A ficha foi atualizada!');
    } catch (e) { console.error(e); alert("Erro ao salvar."); }
}

async function uploadModule(event) {
    const file = event.target.files[0]; if (!file) return;
    appendMessage('Sistema', 'A processar as páginas do módulo PDF...');
    const formData = new FormData(); formData.append('file', file);
    try {
        const res = await fetch("http://localhost:8000/api/upload_module", { method: "POST", body: formData });
        if (!res.ok) throw new Error();
        appendMessage('Sistema', `O módulo '${file.name}' foi memorizado com sucesso!`);
    } catch (e) { console.error(e); appendMessage('Sistema', '<span class="text-red-400">Erro ao carregar o módulo.</span>'); }
    event.target.value = '';
}