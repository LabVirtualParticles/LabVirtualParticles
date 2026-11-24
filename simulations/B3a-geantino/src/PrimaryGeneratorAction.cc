//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
/// \file B3/B3a/src/PrimaryGeneratorAction.cc
/// \brief Implementation of the B3::PrimaryGeneratorAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026 — ver o .hh.

#include "PrimaryGeneratorAction.hh"

#include "G4ChargedGeantino.hh"
#include "G4GenericMessenger.hh"
#include "G4IonTable.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

namespace B3
{

PrimaryGeneratorAction::PrimaryGeneratorAction()
  : fSourceCentre(4 * cm, 4 * cm, 4 * cm), fSourceSize(1 * cm)
{
  G4int n_particle = 1;
  fParticleGun = new G4ParticleGun(n_particle);

  // default particle kinematic

  G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
  G4ParticleDefinition* particle = particleTable->FindParticle("chargedgeantino");
  fParticleGun->SetParticleDefinition(particle);
  fParticleGun->SetParticlePosition(G4ThreeVector(0., 0., 0.));
  fParticleGun->SetParticleEnergy(1 * eV);
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(1., 0., 0.));

  // Comandos de macro usados pelo backend do site
  fMessenger = new G4GenericMessenger(this, "/geantino/source/",
                                      "Regiao onde a fonte radioativa e sorteada");
  fMessenger->DeclarePropertyWithUnit("centre", "cm", fSourceCentre,
                                      "Centro da regiao da fonte");
  auto& sizeCmd = fMessenger->DeclarePropertyWithUnit(
    "size", "cm", fSourceSize, "Aresta do cubo onde a posicao inicial e sorteada");
  sizeCmd.SetParameterName("size", false);
  sizeCmd.SetRange("size>=0.");
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fMessenger;
  delete fParticleGun;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  G4ParticleDefinition* particle = fParticleGun->GetParticleDefinition();
  if (particle == G4ChargedGeantino::ChargedGeantino()) {
    // fluorine
    G4int Z = 9, A = 18;
    G4double ionCharge = 0. * eplus;
    G4double excitEnergy = 0. * keV;

    G4ParticleDefinition* ion = G4IonTable::GetIonTable()->GetIon(Z, A, excitEnergy);
    fParticleGun->SetParticleDefinition(ion);
    fParticleGun->SetParticleCharge(ionCharge);
  }

  // randomized position (no original: x0=y0=z0=4 cm, dx0=dy0=dz0=1 cm)
  //
  G4double x0 = fSourceCentre.x(), y0 = fSourceCentre.y(), z0 = fSourceCentre.z();
  G4double dx0 = fSourceSize, dy0 = fSourceSize, dz0 = fSourceSize;
  x0 += dx0 * (G4UniformRand() - 0.5);
  y0 += dy0 * (G4UniformRand() - 0.5);
  z0 += dz0 * (G4UniformRand() - 0.5);
  fParticleGun->SetParticlePosition(G4ThreeVector(x0, y0, z0));

  // create vertex
  //
  fParticleGun->GeneratePrimaryVertex(event);
}

}  // namespace B3
