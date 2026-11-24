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
/// \file B5/include/RunAction.hh
/// \brief Definition of the B5::RunAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026: no lugar dos histogramas
/// e da ntuple em ROOT do original, a run grava os arquivos lidos pelo
/// backend do site, no diretorio de trabalho:
///   - geometria.gdml   (inicio da run)
///   - trajetorias.json (fim da run, via Geantino::TrajectoryRecorder)
///   - resultados.json  (fim da run: as mesmas grandezas da ntuple do
///                       original, evento por evento)

#ifndef B5RunAction_h
#define B5RunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"

#include <vector>

class G4Run;

namespace B5
{

/// O que o original gravava na ntuple "B5", por evento, + a particula e o
/// momento primarios.
struct EventRecord
{
    G4int event = 0;
    G4String particle;
    G4double momentum = 0.;  // modulo do momento primario
    G4int dc1Hits = 0, dc2Hits = 0;
    G4double emEdep = 0., hadEdep = 0.;
    G4int emCells = 0, hadCells = 0;
    G4double time1 = -1., time2 = -1.;  // < 0: hodoscopio sem acerto
};

/// Run action class

class RunAction : public G4UserRunAction
{
  public:
    RunAction() = default;
    ~RunAction() override = default;

    void BeginOfRunAction(const G4Run*) override;
    void EndOfRunAction(const G4Run*) override;

    void AddEvent(const EventRecord& record) { fEvents.push_back(record); }

  private:
    void WriteResultsJSON(const G4Run* run) const;

    std::vector<EventRecord> fEvents;
};

}  // namespace B5

#endif
