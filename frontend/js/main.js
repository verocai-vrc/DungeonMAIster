let ws;
let currentCharacterData = null;
let currentEditInventory = [];
let currentEditSpells = [];
let currentEditResources = {};
let currentEditSpellSlots = {};
let lastAppliedRace = null;

// --- TAB SYSTEM ---
function switchTab(tabId) {
    ['sheet', 'inventory', 'abilities', 'system'].forEach(id => {
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
        appendMessage('System', 'You are already connected to the server.');
        return;
    }
    ws = new WebSocket("ws://localhost:8000/ws");
    ws.onopen = () => {
        document.getElementById('ws-status').textContent = 'Connected';
        document.getElementById('ws-status').className = 'text-sm text-green-400 font-bold';
        appendMessage('System', 'Connection established with the DungeonMAIster server.');
    };
    ws.onmessage = (event) => {
        appendMessage('Game Master', event.data);
        // Only reload the sheet when the backend signals that the state changed (HP, AC, Inventory, etc)
        if (event.data.includes('STATE_CHANGED')) loadCharacter(true);
    };
    ws.onclose = () => {
        document.getElementById('ws-status').textContent = 'Disconnected';
        document.getElementById('ws-status').className = 'text-sm text-red-400 font-bold';
        appendMessage('System', 'The connection to the server was lost.');
    };
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("Please connect to the AI Game Master first in the 'System' tab."); return;
    }
    appendMessage('Player', message);
    ws.send(message);
    input.value = '';
}

function handleKeyPress(event) { if (event.key === 'Enter') sendMessage(); }

function appendMessage(sender, text) {
    const history = document.getElementById('chat-history');
    const div = document.createElement('div');
    const isPlayer = sender === 'Player';
    const isSystem = sender === 'System';

    if (!isPlayer && !isSystem) {
        const rollRegex = /\[REQUEST_ROLL(?:.*?)?\]/g;
        text = text.replace(rollRegex, () => {
            const uniqueId = 'roll-desc-' + Math.random().toString(36).substr(2, 9);
            return `
            <div class="mt-4 border-t border-gray-700 pt-3 space-y-2">
                <p class="text-xs text-gray-400 uppercase font-bold">The Game Master requested a check. How do you want to act?</p>
                <input type="text" id="${uniqueId}" placeholder="e.g. I try to intimidate with force..." class="w-full bg-gray-900 text-white px-3 py-2 rounded border border-gray-600 focus:outline-none focus:border-blue-500 text-sm">
                <div class="grid grid-cols-3 sm:grid-cols-6 gap-1">
                    <button onclick="sendAttrRoll('STR', '${uniqueId}')" class="bg-red-900/80 hover:bg-red-700 text-white py-1 rounded text-xs font-bold transition">STR</button>
                    <button onclick="sendAttrRoll('DEX', '${uniqueId}')" class="bg-green-900/80 hover:bg-green-700 text-white py-1 rounded text-xs font-bold transition">DEX</button>
                    <button onclick="sendAttrRoll('CON', '${uniqueId}')" class="bg-orange-900/80 hover:bg-orange-700 text-white py-1 rounded text-xs font-bold transition">CON</button>
                    <button onclick="sendAttrRoll('INT', '${uniqueId}')" class="bg-blue-900/80 hover:bg-blue-700 text-white py-1 rounded text-xs font-bold transition">INT</button>
                    <button onclick="sendAttrRoll('WIS', '${uniqueId}')" class="bg-indigo-900/80 hover:bg-indigo-700 text-white py-1 rounded text-xs font-bold transition">WIS</button>
                    <button onclick="sendAttrRoll('CHA', '${uniqueId}')" class="bg-pink-900/80 hover:bg-pink-700 text-white py-1 rounded text-xs font-bold transition">CHA</button>
                </div>
            </div>`;
        });
    }

    div.className = `p-3 rounded-lg w-max max-w-[85%] ${isPlayer ? 'bg-blue-900/40 text-blue-100 self-end ml-auto border border-blue-800/50' : (isSystem ? 'bg-gray-800 text-gray-400 self-center text-sm' : 'bg-gray-800 text-gray-200 self-start border border-gray-700')}`;
    div.innerHTML = `<span class="font-bold block text-xs opacity-75 mb-1 ${isPlayer ? 'text-blue-300' : (isSystem ? 'text-gray-500' : 'text-yellow-400')}">${sender}</span><span>${text}</span>`;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

function sendRoll(expr) {
    if (!ws || ws.readyState !== WebSocket.OPEN) { alert("Please connect to the AI Game Master."); return; }
    ws.send(`/roll ${expr}`);
}

function sendAttrRoll(attr, inputId) {
    if (!ws || ws.readyState !== WebSocket.OPEN) { alert("Please connect to the AI Game Master."); return; }
    const descInput = document.getElementById(inputId);
    const desc = descInput ? descInput.value.trim() : "";

    const displayMsg = desc ? `Action with ${attr}: ${desc}` : `I make a ${attr} check.`;
    appendMessage('Player', displayMsg);

    ws.send(`/roll${attr} ${desc}`);

    if (descInput) descInput.disabled = true;
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
    const desc = (dndRules && dndRules.descriptions && dndRules.descriptions[name]) ? dndRules.descriptions[name] : "No description available.";
    return `<li class="relative group w-max list-none mb-1">
        <span onclick="quickRoll('${name.replace(/'/g, "\\'")}', false)" class="inline-flex items-center gap-2 cursor-pointer"><span class="text-blue-500 text-xs hover:text-blue-400">✦</span><span class="border-b border-dashed border-gray-500 hover:text-blue-300 transition">${name}</span></span>
        <div class="absolute left-6 top-full mt-1 hidden group-hover:block w-64 bg-gray-950 text-gray-300 text-xs rounded p-3 shadow-xl border border-gray-700 z-[60] pointer-events-none">
            <strong class="text-blue-400 block mb-1 border-b border-gray-700 pb-1">${name}</strong>${desc}
        </div>
    </li>`;
}

async function loadCharacter(silent = false) {
    try {
        const response = await fetch("http://localhost:8000/api/character");
        if (!response.ok) throw new Error("Network error");
        const data = await response.json();
        currentCharacterData = data;

        document.getElementById('char-name').textContent = data.name;
        document.getElementById('char-race').textContent = data.race;
        document.getElementById('char-class').textContent = data.character_class;
        document.getElementById('char-level').textContent = data.level;
        document.getElementById('char-xp').textContent = data.xp !== undefined ? data.xp : 0;
        document.getElementById('char-location').textContent = data.location + (data.in_combat ? " ⚔️ (In Combat)" : "");
        document.getElementById('char-hp').textContent = `${data.current_hp} / ${data.max_hp}`;
        document.getElementById('char-ac').textContent = data.armor_class;

        const attrDiv = document.getElementById('char-attributes');
        attrDiv.innerHTML = '';
        const attrs = [
            { name: "STR", val: data.attributes.strength, mod: data.attributes.str_mod },
            { name: "DEX", val: data.attributes.dexterity, mod: data.attributes.dex_mod },
            { name: "CON", val: data.attributes.constitution, mod: data.attributes.con_mod },
            { name: "INT", val: data.attributes.intelligence, mod: data.attributes.int_mod },
            { name: "WIS", val: data.attributes.wisdom, mod: data.attributes.wis_mod },
            { name: "CHA", val: data.attributes.charisma, mod: data.attributes.cha_mod }
        ];
        attrs.forEach(a => {
            attrDiv.innerHTML += `<div onclick="quickRoll('${a.name}', true, ${a.mod})" class="bg-gray-800 p-3 border border-gray-700 rounded flex justify-between items-center cursor-pointer hover:bg-gray-700 transition" title="Roll ${a.name} Check"><span class="font-bold text-gray-400 pointer-events-none">${a.name}</span><div class="text-right pointer-events-none"><span class="text-xl font-semibold text-gray-200">${a.val}</span><span class="text-sm text-gray-500 ml-2">(${a.mod >= 0 ? '+'+a.mod : a.mod})</span></div></div>`;
        });

        const actDiv = document.getElementById('char-actions');
        if (data.in_combat) {
            actDiv.classList.remove('hidden');
            document.getElementById('act-main').className = `flex-1 p-2 rounded transition ${data.action_economy.main ? 'bg-green-700 text-white shadow-sm' : 'bg-gray-800 text-gray-500 line-through'}`;
            document.getElementById('act-bonus').className = `flex-1 p-2 rounded transition ${data.action_economy.bonus ? 'bg-green-700 text-white shadow-sm' : 'bg-gray-800 text-gray-500 line-through'}`;
            document.getElementById('act-react').className = `flex-1 p-2 rounded transition ${data.action_economy.reaction ? 'bg-green-700 text-white shadow-sm' : 'bg-gray-800 text-gray-500 line-through'}`;
        } else { actDiv.classList.add('hidden'); }

        const resContainer = document.getElementById('char-resources');
        resContainer.innerHTML = '';
        if (data.resources && Object.keys(data.resources).length > 0) {
            Object.keys(data.resources).forEach(k => {
                resContainer.innerHTML += `<div class="bg-gray-800 p-2 text-sm rounded border border-gray-700 flex justify-between items-center"><span>${k}</span> <span class="font-bold text-blue-400 bg-gray-900 px-2 py-1 rounded">${data.resources[k].current} / ${data.resources[k].max}</span></div>`;
            });
        }

        const slotsContainer = document.getElementById('char-spellslots');
        slotsContainer.innerHTML = '';
        if (data.spell_slots && Object.keys(data.spell_slots).length > 0) {
            Object.keys(data.spell_slots).forEach(k => {
                slotsContainer.innerHTML += `<div class="bg-purple-900/40 p-2 text-sm rounded border border-purple-800/50 flex justify-between items-center"><span class="text-purple-300">Spell Slot Level ${k}</span> <span class="font-bold text-purple-300 bg-gray-900 px-2 py-1 rounded">${data.spell_slots[k].current} / ${data.spell_slots[k].max}</span></div>`;
            });
        }

        const invUl = document.getElementById('char-inventory');
        invUl.innerHTML = data.inventory.map(item => renderTooltipItem(item)).join('');
        if(data.inventory.length === 0) invUl.innerHTML = '<li class="text-gray-500 italic text-sm p-1 list-none">Empty.</li>';

        const spellsContainer = document.getElementById('spells-container');
        if (data.spells && data.spells.length > 0) {
            spellsContainer.innerHTML = `<ul class="space-y-1 text-sm text-gray-400 bg-gray-800 p-3 rounded border border-gray-700 shadow-inner">${data.spells.map(spell => renderTooltipItem(spell)).join('')}</ul>`;
        } else { spellsContainer.innerHTML = '<div class="text-gray-500 italic text-sm">No spells on the sheet.</div>'; }

        const featsUl = document.getElementById('char-features');
        featsUl.innerHTML = data.features.map(feat => renderTooltipItem(feat)).join('');
        if(data.features.length === 0) featsUl.innerHTML = '<li class="text-gray-500 italic list-none">No features.</li>';

        if (!silent) switchTab('sheet');
    } catch (error) {
        console.error(error);
        if (!silent) alert("Error loading the sheet. Check the backend.");
    }
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
            if (dndRules.equipment) {
                Object.keys(dndRules.equipment).forEach(item => { inventorySelect.add(new Option(item, item)); });
            }

            const spellSelect = document.getElementById('add-spell-select');
            if (dndRules.spells && Object.keys(dndRules.spells).length > 0) {
                Object.keys(dndRules.spells).forEach(level => {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = `Level ${level}`;
                    dndRules.spells[level].forEach(spell => { optgroup.appendChild(new Option(spell, spell)); });
                    spellSelect.appendChild(optgroup);
                });
            }
        }
    } catch (error) { console.error("Error loading the rules:", error); }
}
window.addEventListener('DOMContentLoaded', async () => {
    await fetchRules();
    loadCharacter(true); // Load the sheet after the rules to ensure the descriptions are available
});

function updateInventoryUI() {
    const list = document.getElementById('edit-inventory-list');
    list.innerHTML = currentEditInventory.map((item, index) =>
        `<li class="flex justify-between items-center bg-gray-800 p-1 px-2 rounded"><span>${item}</span><button type="button" onclick="removeInventoryItem(${index})" class="text-red-400 hover:text-red-300 font-bold px-2 text-lg leading-none">&times;</button></li>`
    ).join('');
    if (currentEditInventory.length === 0) list.innerHTML = '<li class="text-gray-500 italic text-sm p-1">Inventory empty.</li>';
}

function addInventoryItem() {
    const item = document.getElementById('add-inventory-select').value;
    if (item) { currentEditInventory.push(item); updateInventoryUI(); updateAutoFeatures(); }
}
function removeInventoryItem(index) { currentEditInventory.splice(index, 1); updateInventoryUI(); updateAutoFeatures(); }

function updateSpellsUI() {
    const list = document.getElementById('edit-spells-list');
    list.innerHTML = currentEditSpells.map((item, index) =>
        `<li class="flex justify-between items-center bg-gray-800 p-1 px-2 rounded"><span>${item}</span><button type="button" onclick="removeSpellItem(${index})" class="text-red-400 hover:text-red-300 font-bold px-2 text-lg leading-none">&times;</button></li>`
    ).join('');
    if (currentEditSpells.length === 0) list.innerHTML = '<li class="text-gray-500 italic text-sm p-1">No spells.</li>';
}

function addSpellItem() {
    const item = document.getElementById('add-spell-select').value;
    if (item) { currentEditSpells.push(item); updateSpellsUI(); }
}
function removeSpellItem(index) { currentEditSpells.splice(index, 1); updateSpellsUI(); }

function updateAutoFeatures() {
    if (!dndRules) return;
    currentEditResources = {};
    currentEditSpellSlots = {};

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

    if (cls === "Barbarian") {
        let rages = lvl >= 6 ? 4 : (lvl >= 3 ? 3 : 2);
        currentEditResources["Rage"] = {max: rages, current: rages};
    }
    if (["Wizard", "Cleric", "Sorcerer"].includes(cls)) {
        // Official full-caster spell slot table, index = character level (1-20)
        const slots = [
            {},
            {"1":2}, {"1":3}, {"1":4,"2":2}, {"1":4,"2":3}, {"1":4,"2":3,"3":2},
            {"1":4,"2":3,"3":3}, {"1":4,"2":3,"3":3,"4":1}, {"1":4,"2":3,"3":3,"4":2}, {"1":4,"2":3,"3":3,"4":3,"5":1}, {"1":4,"2":3,"3":3,"4":3,"5":2},
            {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1}, {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1}, {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1,"7":1}, {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1,"7":1}, {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1,"7":1,"8":1},
            {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1,"7":1,"8":1}, {"1":4,"2":3,"3":3,"4":3,"5":2,"6":1,"7":1,"8":1,"9":1}, {"1":4,"2":3,"3":3,"4":3,"5":3,"6":1,"7":1,"8":1,"9":1}, {"1":4,"2":3,"3":3,"4":3,"5":3,"6":2,"7":1,"8":1,"9":1}, {"1":4,"2":3,"3":3,"4":3,"5":3,"6":2,"7":2,"8":1,"9":1}
        ];
        const lvlSlots = slots[Math.min(Math.max(lvl, 1), 20)];
        Object.keys(lvlSlots).forEach(k => {
            currentEditSpellSlots[k] = {max: lvlSlots[k], current: lvlSlots[k]};
        });
    }

    const classData = dndRules.classes[cls];
    if (classData) {
        if (classData.proficiencies) autoFeats.push(`Skills: ${classData.proficiencies.join(", ")}`);
        if (classData.features) {
            for (let i = 1; i <= lvl; i++) {
                if (classData.features[i]) autoFeats.push(...classData.features[i]);
            }
        }
    }
    if (lvl > 3) autoFeats.push(`More ${cls} class features at level ${lvl}`);
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
    if (dndRules.equipment) {
        currentEditInventory.forEach(item => {
            const eqData = dndRules.equipment[item];
            if (eqData && eqData.status) {
                if (eqData.type === 'Shield' || eqData.status.ac_bonus) { hasShield = true; }
                else if (eqData.type === 'Armor') {
                    let calcAC = eqData.status.base_ac || 10;
                    if (eqData.status.armor_type === 'light') calcAC += dexMod;
                    else if (eqData.status.armor_type === 'medium') calcAC += Math.min(dexMod, 2);
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
        title.textContent = "New Sheet";
        ['edit-name','edit-inventory','edit-location'].forEach(id => document.getElementById(id).value = id === 'edit-location' ? "Unknown" : "");
        ['edit-race','edit-class'].forEach(id => document.getElementById(id).selectedIndex = 0);
        ['edit-level','edit-max-hp','edit-current-hp','edit-ac','edit-str','edit-dex','edit-con','edit-int','edit-wis','edit-cha'].forEach(id => document.getElementById(id).value = (id === 'edit-level') ? "1" : "10");
        currentEditInventory = []; updateInventoryUI(); currentEditSpells = []; updateSpellsUI(); currentEditResources = {}; currentEditSpellSlots = {}; lastAppliedRace = null; updateAutoFeatures();
    } else {
        title.textContent = "Edit Sheet";
        const d = currentCharacterData;
        document.getElementById('edit-name').value = d.name; document.getElementById('edit-race').value = d.race; document.getElementById('edit-class').value = d.character_class;
        document.getElementById('edit-level').value = d.level; document.getElementById('edit-xp').value = d.xp !== undefined ? d.xp : 0; document.getElementById('edit-location').value = d.location;
        document.getElementById('edit-max-hp').value = d.max_hp; document.getElementById('edit-current-hp').value = d.current_hp; document.getElementById('edit-ac').value = d.armor_class;
        document.getElementById('edit-str').value = d.attributes.strength; document.getElementById('edit-dex').value = d.attributes.dexterity; document.getElementById('edit-con').value = d.attributes.constitution;
        document.getElementById('edit-int').value = d.attributes.intelligence; document.getElementById('edit-wis').value = d.attributes.wisdom; document.getElementById('edit-cha').value = d.attributes.charisma;
        currentEditInventory = [...d.inventory]; updateInventoryUI(); currentEditSpells = d.spells ? [...d.spells] : []; updateSpellsUI(); lastAppliedRace = d.race; document.getElementById('edit-features').value = d.features.join(", ");
        currentEditResources = d.resources ? JSON.parse(JSON.stringify(d.resources)) : {};
        currentEditSpellSlots = d.spell_slots ? JSON.parse(JSON.stringify(d.spell_slots)) : {};
    }
    document.getElementById('char-modal').classList.remove('hidden');
}

function closeEditModal() { document.getElementById('char-modal').classList.add('hidden'); }

async function saveCharacter() {
    const payload = {
        name: document.getElementById('edit-name').value || "Hero", race: document.getElementById('edit-race').value || "Human",
        character_class: document.getElementById('edit-class').value || "Adventurer", level: parseInt(document.getElementById('edit-level').value) || 1, xp: parseInt(document.getElementById('edit-xp').value) || 0,
        location: document.getElementById('edit-location').value || "Unknown", max_hp: parseInt(document.getElementById('edit-max-hp').value) || 10,
        current_hp: parseInt(document.getElementById('edit-current-hp').value) || 10, armor_class: parseInt(document.getElementById('edit-ac').value) || 10,
        inventory: currentEditInventory, spells: currentEditSpells, features: document.getElementById('edit-features').value.split(',').map(i => i.trim()).filter(i => i !== ''),
        resources: currentEditResources, spell_slots: currentEditSpellSlots,
        attributes: { strength: parseInt(document.getElementById('edit-str').value) || 10, dexterity: parseInt(document.getElementById('edit-dex').value) || 10, constitution: parseInt(document.getElementById('edit-con').value) || 10, intelligence: parseInt(document.getElementById('edit-int').value) || 10, wisdom: parseInt(document.getElementById('edit-wis').value) || 10, charisma: parseInt(document.getElementById('edit-cha').value) || 10 },
        in_combat: currentCharacterData ? currentCharacterData.in_combat : false,
        initiative_order: currentCharacterData ? currentCharacterData.initiative_order : []
    };
    try {
        const res = await fetch("http://localhost:8000/api/character", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        if (!res.ok) throw new Error();
        closeEditModal(); loadCharacter(); appendMessage('System', 'The sheet has been updated!');
    } catch (e) { console.error(e); alert("Error saving."); }
}

async function uploadModule(event) {
    const file = event.target.files[0]; if (!file) return;
    appendMessage('System', 'Processing the PDF module pages...');
    const formData = new FormData(); formData.append('file', file);
    try {
        const res = await fetch("http://localhost:8000/api/upload_module", { method: "POST", body: formData });
        if (!res.ok) throw new Error();
        appendMessage('System', `Module '${file.name}' was memorized successfully!`);
    } catch (e) { console.error(e); appendMessage('System', '<span class="text-red-400">Error loading the module.</span>'); }
    event.target.value = '';
}
